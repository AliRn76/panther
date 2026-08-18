//! The websocket half of the ASGI bridge: handshake, upgrade, and frame pumping.

use std::net::SocketAddr;
use std::sync::Arc;

use base64::Engine;
use bytes::Bytes;
use futures_util::{SinkExt, StreamExt};
use http::{header, HeaderName, HeaderValue, Request, Response, StatusCode};
use http_body_util::{BodyExt, Empty};
use hyper::body::Incoming;
use hyper_util::rt::TokioIo;
use sha1::{Digest, Sha1};
use tokio::sync::mpsc;
use tokio_tungstenite::tungstenite::protocol::frame::coding::CloseCode;
use tokio_tungstenite::tungstenite::protocol::{CloseFrame, Message, Role};
use tokio_tungstenite::WebSocketStream;

use crate::asgi::{ConnectionKind, PendingConnection, RxMessage, ScopeData, TxMessage};
use crate::server::{simple_response, ServerBody, ServerState};

const WS_GUID: &[u8] = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

/// Headers the server owns; an application must not be able to override them
/// through `websocket.accept`.
const RESERVED_HEADERS: [&str; 4] = [
    "connection",
    "upgrade",
    "sec-websocket-accept",
    "sec-websocket-protocol",
];

fn header_is(request: &Request<Incoming>, name: header::HeaderName, expected: &str) -> bool {
    request
        .headers()
        .get(name)
        .and_then(|value| value.to_str().ok())
        .map(|value| {
            value
                .split(',')
                .any(|token| token.trim().eq_ignore_ascii_case(expected))
        })
        .unwrap_or(false)
}

pub fn is_upgrade_request(request: &Request<Incoming>) -> bool {
    request.method() == http::Method::GET
        && header_is(request, header::UPGRADE, "websocket")
        && header_is(request, header::CONNECTION, "upgrade")
        && request.headers().contains_key(header::SEC_WEBSOCKET_KEY)
}

fn derive_accept_key(key: &[u8]) -> String {
    let mut hasher = Sha1::new();
    hasher.update(key);
    hasher.update(WS_GUID);
    base64::engine::general_purpose::STANDARD.encode(hasher.finalize())
}

fn empty_body() -> ServerBody {
    Empty::<Bytes>::new()
        .map_err(|never| match never {})
        .boxed()
}

pub async fn handle(
    state: Arc<ServerState>,
    mut request: Request<Incoming>,
    peer: Option<SocketAddr>,
    local: Option<SocketAddr>,
) -> Option<Response<ServerBody>> {
    let Some(key) = request
        .headers()
        .get(header::SEC_WEBSOCKET_KEY)
        .map(|value| value.as_bytes().to_vec())
    else {
        return Some(simple_response(
            StatusCode::BAD_REQUEST,
            "Missing Sec-WebSocket-Key",
        ));
    };

    let version_supported = request
        .headers()
        .get(header::SEC_WEBSOCKET_VERSION)
        .map(|value| value.as_bytes() == b"13")
        .unwrap_or(false);
    if !version_supported {
        return Response::builder()
            .status(StatusCode::UPGRADE_REQUIRED)
            .header("sec-websocket-version", "13")
            .body(empty_body())
            .ok();
    }

    // Must be taken before the request is consumed by `into_parts()`.
    let upgrade = hyper::upgrade::on(&mut request);
    let (parts, _) = request.into_parts();
    let scope = ScopeData::new(
        ConnectionKind::Websocket,
        &parts,
        peer,
        local,
        &state.root_path,
    );

    let (in_tx, in_rx) = mpsc::channel::<RxMessage>(state.message_buffer);
    let (out_tx, mut out_rx) = mpsc::channel::<TxMessage>(state.message_buffer);

    let published = state
        .publish(PendingConnection {
            scope,
            rx: in_rx,
            tx: out_tx,
        })
        .await;
    if !published {
        return Some(simple_response(
            StatusCode::SERVICE_UNAVAILABLE,
            "Server is not accepting connections",
        ));
    }

    // ASGI opens every websocket scope with a `websocket.connect` message.
    if in_tx.send(RxMessage::WsConnect).await.is_err() {
        return None;
    }

    // The application answers with either `websocket.accept` or `websocket.close`.
    let accepted = loop {
        match out_rx.recv().await {
            Some(TxMessage::WsAccept {
                subprotocol,
                headers,
            }) => break Some((subprotocol, headers)),
            Some(TxMessage::WsClose { .. }) | None => break None,
            Some(_) => continue,
        }
    };

    let Some((subprotocol, extra_headers)) = accepted else {
        // A close before the handshake completes is a denial, which on the wire
        // is an ordinary HTTP response rather than a websocket close frame.
        return Some(simple_response(
            StatusCode::FORBIDDEN,
            "WebSocket connection rejected",
        ));
    };

    let mut builder = Response::builder()
        .status(StatusCode::SWITCHING_PROTOCOLS)
        .header(header::CONNECTION, "upgrade")
        .header(header::UPGRADE, "websocket")
        .header("sec-websocket-accept", derive_accept_key(&key));

    if let Some(subprotocol) = subprotocol.as_deref() {
        builder = builder.header("sec-websocket-protocol", subprotocol);
    }
    for (name, value) in extra_headers {
        let Ok(name) = HeaderName::from_bytes(&name) else {
            continue;
        };
        if RESERVED_HEADERS.contains(&name.as_str()) {
            continue;
        }
        let Ok(value) = HeaderValue::from_bytes(&value) else {
            continue;
        };
        builder = builder.header(name, value);
    }

    tokio::spawn(pump(upgrade, in_tx, out_rx));

    builder.body(empty_body()).ok()
}

async fn pump(
    upgrade: hyper::upgrade::OnUpgrade,
    in_tx: mpsc::Sender<RxMessage>,
    mut out_rx: mpsc::Receiver<TxMessage>,
) {
    let upgraded = match upgrade.await {
        Ok(upgraded) => upgraded,
        Err(_) => {
            let _ = in_tx.send(RxMessage::WsDisconnect { code: 1006 }).await;
            return;
        }
    };

    let socket = WebSocketStream::from_raw_socket(TokioIo::new(upgraded), Role::Server, None).await;
    let (mut sink, mut source) = socket.split();

    // 1006 is the "closed abnormally" code, and is the right default for every
    // path out of this loop that is not an explicit close.
    let mut disconnect_code = 1006u16;

    loop {
        tokio::select! {
            incoming = source.next() => {
                match incoming {
                    Some(Ok(Message::Text(text))) => {
                        if in_tx.send(RxMessage::WsReceiveText(text.as_str().to_owned())).await.is_err() {
                            break;
                        }
                    }
                    Some(Ok(Message::Binary(data))) => {
                        if in_tx.send(RxMessage::WsReceiveBytes(data)).await.is_err() {
                            break;
                        }
                    }
                    Some(Ok(Message::Ping(payload))) => {
                        // Splitting the stream disables tungstenite's automatic
                        // pong, so answer here or clients will time us out.
                        if sink.send(Message::Pong(payload)).await.is_err() {
                            break;
                        }
                    }
                    Some(Ok(Message::Pong(_))) | Some(Ok(Message::Frame(_))) => {}
                    Some(Ok(Message::Close(frame))) => {
                        disconnect_code = frame.map(|f| u16::from(f.code)).unwrap_or(1005);
                        let _ = sink.close().await;
                        break;
                    }
                    Some(Err(_)) | None => break,
                }
            }
            outgoing = out_rx.recv() => {
                match outgoing {
                    Some(TxMessage::WsSendText(text)) => {
                        if sink.send(Message::text(text)).await.is_err() {
                            break;
                        }
                    }
                    Some(TxMessage::WsSendBytes(data)) => {
                        if sink.send(Message::binary(data)).await.is_err() {
                            break;
                        }
                    }
                    Some(TxMessage::WsClose { code, reason }) => {
                        disconnect_code = code;
                        let frame = CloseFrame {
                            code: CloseCode::from(code),
                            reason: reason.into(),
                        };
                        let _ = sink.send(Message::Close(Some(frame))).await;
                        let _ = sink.close().await;
                        break;
                    }
                    // `websocket.accept` arriving twice, or an HTTP message on a
                    // websocket scope: nothing sensible to do, so ignore it.
                    Some(_) => {}
                    None => break,
                }
            }
        }
    }

    let _ = in_tx
        .send(RxMessage::WsDisconnect {
            code: disconnect_code,
        })
        .await;
}
