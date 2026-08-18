//! The HTTP half of the ASGI bridge.

use std::net::SocketAddr;
use std::pin::Pin;
use std::sync::Arc;
use std::task::{Context, Poll};

use bytes::Bytes;
use http::{HeaderName, HeaderValue, Request, Response, StatusCode};
use http_body_util::BodyExt;
use hyper::body::{Body, Frame, Incoming};
use tokio::sync::mpsc;

use crate::asgi::{ConnectionKind, PendingConnection, RxMessage, ScopeData, TxMessage};
use crate::server::{simple_response, ServerBody, ServerState};

/// Response body fed by `http.response.body` messages.
///
/// It also owns a clone of the request-side sender: as long as the body is
/// alive the application's `receive()` will not observe `http.disconnect`,
/// which is what lets streaming responses distinguish "request fully read"
/// from "client went away".
struct AsgiBody {
    out_rx: mpsc::Receiver<TxMessage>,
    _keepalive: mpsc::Sender<RxMessage>,
    done: bool,
}

impl Body for AsgiBody {
    type Data = Bytes;
    type Error = std::io::Error;

    fn poll_frame(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
    ) -> Poll<Option<Result<Frame<Self::Data>, Self::Error>>> {
        let this = self.get_mut();
        loop {
            if this.done {
                return Poll::Ready(None);
            }
            match this.out_rx.poll_recv(cx) {
                Poll::Pending => return Poll::Pending,
                Poll::Ready(None) => {
                    this.done = true;
                    return Poll::Ready(None);
                }
                Poll::Ready(Some(TxMessage::ResponseBody { body, more_body })) => {
                    this.done = !more_body;
                    if body.is_empty() {
                        // Nothing to hand to hyper; either finish or keep waiting.
                        continue;
                    }
                    return Poll::Ready(Some(Ok(Frame::data(body))));
                }
                // A second `http.response.start`, or a websocket message on an
                // HTTP connection: not something we can act on, so ignore it
                // rather than tearing the response down mid-flight.
                Poll::Ready(Some(_)) => continue,
            }
        }
    }
}

pub async fn handle(
    state: Arc<ServerState>,
    request: Request<Incoming>,
    peer: Option<SocketAddr>,
    local: Option<SocketAddr>,
) -> Option<Response<ServerBody>> {
    let (parts, incoming) = request.into_parts();
    let scope = ScopeData::new(ConnectionKind::Http, &parts, peer, local, &state.root_path);

    let (body_tx, body_rx) = mpsc::channel::<RxMessage>(state.message_buffer);
    let (out_tx, mut out_rx) = mpsc::channel::<TxMessage>(state.message_buffer);

    if state
        .accept_tx
        .send(PendingConnection {
            scope,
            rx: body_rx,
            tx: out_tx,
        })
        .await
        .is_err()
    {
        return Some(simple_response(
            StatusCode::SERVICE_UNAVAILABLE,
            "Server is not accepting connections",
        ));
    }

    tokio::spawn(pump_request_body(incoming, body_tx.clone()));

    // ASGI requires `http.response.start` before anything else.
    let start = loop {
        match out_rx.recv().await {
            Some(TxMessage::ResponseStart { status, headers }) => break (status, headers),
            Some(_) => continue,
            None => return None,
        }
    };
    let (status, headers) = start;

    let mut builder = Response::builder().status(StatusCode::from_u16(status).ok()?);
    for (name, value) in headers {
        let Ok(name) = HeaderName::from_bytes(&name) else {
            continue;
        };
        let Ok(value) = HeaderValue::from_bytes(&value) else {
            continue;
        };
        builder = builder.header(name, value);
    }

    let body = AsgiBody {
        out_rx,
        _keepalive: body_tx,
        done: false,
    };

    builder.body(body.boxed()).ok()
}

async fn pump_request_body(mut incoming: Incoming, tx: mpsc::Sender<RxMessage>) {
    loop {
        match incoming.frame().await {
            Some(Ok(frame)) => {
                // Trailers carry nothing ASGI can express; drop them.
                if let Ok(data) = frame.into_data() {
                    if data.is_empty() {
                        continue;
                    }
                    if tx
                        .send(RxMessage::HttpRequest {
                            body: data,
                            more_body: true,
                        })
                        .await
                        .is_err()
                    {
                        return;
                    }
                }
            }
            Some(Err(_)) => {
                let _ = tx.send(RxMessage::HttpDisconnect).await;
                return;
            }
            None => {
                let _ = tx
                    .send(RxMessage::HttpRequest {
                        body: Bytes::new(),
                        more_body: false,
                    })
                    .await;
                return;
            }
        }
    }
}
