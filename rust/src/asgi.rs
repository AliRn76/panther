//! The ASGI data model: scopes, the two message directions, and the `Connection`
//! object that Python drives.
//!
//! Everything here is deliberately plain Rust; the GIL is only taken at the two
//! boundaries (`Connection::receive` resolving a message, `Connection::send`
//! parsing one) so that the hyper/tokio side never blocks on the interpreter.

use std::net::SocketAddr;
use std::sync::Arc;

use bytes::Bytes;
use http::request::Parts;
use http::{HeaderMap, Version};
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PyBytes, PyDict, PyList, PyString, PyTuple};
use tokio::sync::{mpsc, Mutex as AsyncMutex};

/// Which half of the ASGI protocol a connection speaks.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum ConnectionKind {
    Http,
    Websocket,
}

/// Messages produced by the server and consumed by the application's `receive()`.
#[derive(Debug)]
pub enum RxMessage {
    HttpRequest { body: Bytes, more_body: bool },
    HttpDisconnect,
    WsConnect,
    WsReceiveText(String),
    WsReceiveBytes(Bytes),
    WsDisconnect { code: u16 },
}

impl RxMessage {
    fn into_py_dict<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new(py);
        match self {
            RxMessage::HttpRequest { body, more_body } => {
                dict.set_item("type", "http.request")?;
                dict.set_item("body", PyBytes::new(py, &body))?;
                dict.set_item("more_body", more_body)?;
            }
            RxMessage::HttpDisconnect => {
                dict.set_item("type", "http.disconnect")?;
            }
            RxMessage::WsConnect => {
                dict.set_item("type", "websocket.connect")?;
            }
            RxMessage::WsReceiveText(text) => {
                dict.set_item("type", "websocket.receive")?;
                dict.set_item("text", text)?;
                dict.set_item("bytes", py.None())?;
            }
            RxMessage::WsReceiveBytes(data) => {
                dict.set_item("type", "websocket.receive")?;
                dict.set_item("bytes", PyBytes::new(py, &data))?;
                dict.set_item("text", py.None())?;
            }
            RxMessage::WsDisconnect { code } => {
                dict.set_item("type", "websocket.disconnect")?;
                dict.set_item("code", code)?;
            }
        }
        Ok(dict)
    }
}

/// Messages produced by the application's `send()` and consumed by the server.
#[derive(Debug)]
pub enum TxMessage {
    ResponseStart {
        status: u16,
        headers: Vec<(Bytes, Bytes)>,
    },
    ResponseBody {
        body: Bytes,
        more_body: bool,
    },
    WsAccept {
        subprotocol: Option<String>,
        headers: Vec<(Bytes, Bytes)>,
    },
    WsSendText(String),
    WsSendBytes(Bytes),
    WsClose {
        code: u16,
        reason: String,
    },
}

/// Read `message['headers']`.
///
/// ASGI specifies an iterable of `(bytes, bytes)` pairs, but Panther's
/// `Websocket.accept()` passes `headers or {}` — so a mapping has to be accepted
/// too, otherwise every websocket handshake would fail.
fn parse_headers(value: Option<Bound<'_, PyAny>>) -> PyResult<Vec<(Bytes, Bytes)>> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };
    if value.is_none() {
        return Ok(Vec::new());
    }

    let mut headers = Vec::new();

    if let Ok(mapping) = value.downcast::<PyDict>() {
        for (key, val) in mapping.iter() {
            headers.push((coerce_bytes(&key)?, coerce_bytes(&val)?));
        }
        return Ok(headers);
    }

    for item in value.try_iter()? {
        let pair = item?;
        let name = pair
            .get_item(0)
            .map_err(|_| PyValueError::new_err("each header must be a (name, value) pair"))?;
        let value = pair
            .get_item(1)
            .map_err(|_| PyValueError::new_err("each header must be a (name, value) pair"))?;
        headers.push((coerce_bytes(&name)?, coerce_bytes(&value)?));
    }
    Ok(headers)
}

/// Accept `bytes` or `str` wherever ASGI asks for `bytes`; Python code in the
/// wild is loose about this and being strict buys nothing.
fn coerce_bytes(value: &Bound<'_, PyAny>) -> PyResult<Bytes> {
    if let Ok(data) = value.downcast::<PyBytes>() {
        return Ok(Bytes::copy_from_slice(data.as_bytes()));
    }
    if let Ok(text) = value.downcast::<PyString>() {
        return Ok(Bytes::from(text.to_cow()?.into_owned().into_bytes()));
    }
    if let Ok(data) = value.extract::<Vec<u8>>() {
        return Ok(Bytes::from(data));
    }
    Err(PyValueError::new_err("expected `bytes` or `str`"))
}

impl TxMessage {
    fn from_py(message: &Bound<'_, PyAny>) -> PyResult<Self> {
        let msg_type: String = message
            .get_item("type")
            .map_err(|_| PyValueError::new_err("ASGI messages must have a 'type' key"))?
            .extract()?;

        match msg_type.as_str() {
            "http.response.start" => {
                let status: u16 = message.get_item("status")?.extract()?;
                let headers = parse_headers(message.get_item("headers").ok())?;
                Ok(TxMessage::ResponseStart { status, headers })
            }
            "http.response.body" => {
                let body = match message.get_item("body") {
                    Ok(value) if !value.is_none() => coerce_bytes(&value)?,
                    _ => Bytes::new(),
                };
                let more_body = match message.get_item("more_body") {
                    Ok(value) if !value.is_none() => value.extract()?,
                    _ => false,
                };
                Ok(TxMessage::ResponseBody { body, more_body })
            }
            "websocket.accept" => {
                let subprotocol = match message.get_item("subprotocol") {
                    Ok(value) if !value.is_none() => Some(value.extract::<String>()?),
                    _ => None,
                };
                let headers = parse_headers(message.get_item("headers").ok())?;
                Ok(TxMessage::WsAccept {
                    subprotocol,
                    headers,
                })
            }
            "websocket.send" => {
                if let Ok(value) = message.get_item("text") {
                    if !value.is_none() {
                        return Ok(TxMessage::WsSendText(value.extract::<String>()?));
                    }
                }
                if let Ok(value) = message.get_item("bytes") {
                    if !value.is_none() {
                        return Ok(TxMessage::WsSendBytes(coerce_bytes(&value)?));
                    }
                }
                Err(PyValueError::new_err(
                    "'websocket.send' requires either 'text' or 'bytes'",
                ))
            }
            "websocket.close" => {
                let code = match message.get_item("code") {
                    Ok(value) if !value.is_none() => value.extract::<u16>()?,
                    _ => 1000,
                };
                let reason = match message.get_item("reason") {
                    Ok(value) if !value.is_none() => value.extract::<String>()?,
                    _ => String::new(),
                };
                Ok(TxMessage::WsClose { code, reason })
            }
            other => Err(PyValueError::new_err(format!(
                "unsupported ASGI message type: {other!r}"
            ))),
        }
    }
}

/// Everything needed to build the ASGI `scope` dict, captured without the GIL.
#[derive(Debug, Clone)]
pub struct ScopeData {
    pub kind: ConnectionKind,
    pub method: String,
    pub path: String,
    pub raw_path: Bytes,
    pub query_string: Bytes,
    pub headers: Vec<(Bytes, Bytes)>,
    pub http_version: &'static str,
    pub scheme: &'static str,
    pub root_path: String,
    pub client: Option<(String, u16)>,
    pub server: Option<(String, u16)>,
    pub subprotocols: Vec<String>,
}

fn version_str(version: Version) -> &'static str {
    match version {
        Version::HTTP_09 => "0.9",
        Version::HTTP_10 => "1.0",
        Version::HTTP_2 => "2",
        Version::HTTP_3 => "3",
        _ => "1.1",
    }
}

fn collect_headers(headers: &HeaderMap) -> Vec<(Bytes, Bytes)> {
    headers
        .iter()
        .map(|(name, value)| {
            (
                Bytes::from(name.as_str().to_ascii_lowercase().into_bytes()),
                Bytes::copy_from_slice(value.as_bytes()),
            )
        })
        .collect()
}

/// Percent-decode a path segment-wise, mirroring what ASGI servers hand to apps
/// (`scope['path']` is decoded, `scope['raw_path']` is not).
fn decode_path(raw: &str) -> String {
    let bytes = raw.as_bytes();
    let mut out: Vec<u8> = Vec::with_capacity(bytes.len());
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] == b'%' && index + 2 < bytes.len() {
            let hi = (bytes[index + 1] as char).to_digit(16);
            let lo = (bytes[index + 2] as char).to_digit(16);
            if let (Some(hi), Some(lo)) = (hi, lo) {
                out.push((hi * 16 + lo) as u8);
                index += 3;
                continue;
            }
        }
        out.push(bytes[index]);
        index += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

fn subprotocols_of(headers: &HeaderMap) -> Vec<String> {
    headers
        .get("sec-websocket-protocol")
        .and_then(|value| value.to_str().ok())
        .map(|value| {
            value
                .split(',')
                .map(|item| item.trim().to_string())
                .filter(|item| !item.is_empty())
                .collect()
        })
        .unwrap_or_default()
}

impl ScopeData {
    pub fn new(
        kind: ConnectionKind,
        parts: &Parts,
        client: Option<SocketAddr>,
        server: Option<SocketAddr>,
        root_path: &str,
    ) -> Self {
        let raw_path = parts.uri.path().to_string();
        ScopeData {
            kind,
            method: parts.method.as_str().to_string(),
            path: decode_path(&raw_path),
            raw_path: Bytes::from(raw_path.into_bytes()),
            query_string: Bytes::from(parts.uri.query().unwrap_or("").as_bytes().to_vec()),
            headers: collect_headers(&parts.headers),
            http_version: version_str(parts.version),
            scheme: match kind {
                ConnectionKind::Http => "http",
                ConnectionKind::Websocket => "ws",
            },
            root_path: root_path.to_string(),
            client: client.map(|addr| (addr.ip().to_string(), addr.port())),
            server: server.map(|addr| (addr.ip().to_string(), addr.port())),
            subprotocols: match kind {
                ConnectionKind::Websocket => subprotocols_of(&parts.headers),
                ConnectionKind::Http => Vec::new(),
            },
        }
    }

    fn into_py_dict<'py>(self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let scope = PyDict::new(py);

        let asgi = PyDict::new(py);
        asgi.set_item("version", "3.0")?;
        asgi.set_item("spec_version", "2.3")?;
        scope.set_item("asgi", asgi)?;

        scope.set_item(
            "type",
            match self.kind {
                ConnectionKind::Http => "http",
                ConnectionKind::Websocket => "websocket",
            },
        )?;
        scope.set_item("http_version", self.http_version)?;
        scope.set_item("method", self.method)?;
        scope.set_item("scheme", self.scheme)?;
        scope.set_item("path", self.path)?;
        scope.set_item("raw_path", PyBytes::new(py, &self.raw_path))?;
        scope.set_item("root_path", self.root_path)?;
        scope.set_item("query_string", PyBytes::new(py, &self.query_string))?;

        let headers = PyList::empty(py);
        for (name, value) in &self.headers {
            headers.append(PyTuple::new(
                py,
                [PyBytes::new(py, name), PyBytes::new(py, value)],
            )?)?;
        }
        scope.set_item("headers", headers)?;

        match self.client {
            Some((ip, port)) => scope.set_item("client", (ip, port))?,
            None => scope.set_item("client", py.None())?,
        }
        match self.server {
            Some((ip, port)) => scope.set_item("server", (ip, port))?,
            None => scope.set_item("server", py.None())?,
        }

        if self.kind == ConnectionKind::Websocket {
            scope.set_item("subprotocols", self.subprotocols)?;
        }

        scope.set_item("state", PyDict::new(py))?;
        Ok(scope)
    }
}

/// A connection handed over to Python, still unbuilt: the scope dict is only
/// materialised once `Server.accept()` returns it to the event loop thread.
pub struct PendingConnection {
    pub scope: ScopeData,
    pub rx: mpsc::Receiver<RxMessage>,
    pub tx: mpsc::Sender<TxMessage>,
}

/// The Python-facing handle for one HTTP request or one websocket session.
///
/// `receive` and `send` are the two ASGI callables; both return awaitables that
/// resolve on the tokio runtime and are completed back on the asyncio loop by
/// `pyo3-async-runtimes`.
#[pyclass(module = "panther_server")]
pub struct Connection {
    #[pyo3(get)]
    scope: Py<PyDict>,
    kind: ConnectionKind,
    rx: Arc<AsyncMutex<mpsc::Receiver<RxMessage>>>,
    tx: mpsc::Sender<TxMessage>,
}

impl Connection {
    pub fn from_pending(py: Python<'_>, pending: PendingConnection) -> PyResult<Self> {
        let kind = pending.scope.kind;
        let scope = pending.scope.into_py_dict(py)?.unbind();
        Ok(Connection {
            scope,
            kind,
            rx: Arc::new(AsyncMutex::new(pending.rx)),
            tx: pending.tx,
        })
    }
}

#[pymethods]
impl Connection {
    /// The ASGI `receive` callable.
    fn receive<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let rx = self.rx.clone();
        let kind = self.kind;
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let message = {
                let mut guard = rx.lock().await;
                guard.recv().await
            };
            // A closed channel means the peer is gone; ASGI wants an explicit
            // disconnect message rather than a hang.
            let message = message.unwrap_or(match kind {
                ConnectionKind::Http => RxMessage::HttpDisconnect,
                ConnectionKind::Websocket => RxMessage::WsDisconnect { code: 1006 },
            });
            Python::attach(|py| Ok(message.into_py_dict(py)?.into_any().unbind()))
        })
    }

    /// The ASGI `send` callable.
    fn send<'py>(
        &self,
        py: Python<'py>,
        message: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        // Parse eagerly: a malformed message should raise inside the caller's
        // `await send(...)` rather than being swallowed by the server task.
        let parsed = TxMessage::from_py(message)?;
        let tx = self.tx.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            tx.send(parsed)
                .await
                .map_err(|_| PyRuntimeError::new_err("connection is closed"))?;
            Ok(())
        })
    }

    #[getter]
    fn kind(&self) -> &'static str {
        match self.kind {
            ConnectionKind::Http => "http",
            ConnectionKind::Websocket => "websocket",
        }
    }

    fn __repr__(&self) -> String {
        format!("<panther_server.Connection kind={}>", self.kind())
    }
}
