//! Listener, connection dispatch and the Python-facing `Server` object.

use std::net::SocketAddr;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex as StdMutex};

use bytes::Bytes;
use http::{Request, Response, StatusCode};
use http_body_util::combinators::BoxBody;
use http_body_util::{BodyExt, Full};
use hyper::body::Incoming;
use hyper::service::service_fn;
use hyper_util::rt::TokioIo;
use pyo3::exceptions::{PyOSError, PyRuntimeError};
use pyo3::prelude::*;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{mpsc, watch, Mutex as AsyncMutex};

use crate::asgi::{Connection, PendingConnection};
use crate::http_handler;
use crate::websocket;

/// Body type used for every response this server produces.
pub type ServerBody = BoxBody<Bytes, std::io::Error>;

pub fn simple_response(status: StatusCode, message: &'static str) -> Response<ServerBody> {
    Response::builder()
        .status(status)
        .header(http::header::CONTENT_TYPE, "text/plain; charset=utf-8")
        .body(
            Full::new(Bytes::from_static(message.as_bytes()))
                .map_err(|never| match never {})
                .boxed(),
        )
        .expect("static response is always valid")
}

pub struct ServerState {
    pub root_path: String,
    pub accept_tx: mpsc::Sender<PendingConnection>,
    pub message_buffer: usize,
    pub local_addr: StdMutex<Option<SocketAddr>>,
    pub shutdown_tx: watch::Sender<bool>,
    pub shutdown_rx: watch::Receiver<bool>,
    pub active_connections: AtomicU64,
}

impl ServerState {
    pub fn is_shutting_down(&self) -> bool {
        *self.shutdown_rx.borrow()
    }

    /// Hand a connection to Python, waiting for room in the queue.
    ///
    /// Returns `false` when the connection could not be published. The wait is
    /// cancelled by shutdown: once Python stops calling `accept()` nothing will
    /// drain the queue again, and a plain `send().await` would hang the request
    /// forever instead of letting hyper answer and close.
    pub async fn publish(&self, pending: PendingConnection) -> bool {
        let mut shutdown = self.shutdown_rx.clone();
        tokio::select! {
            biased;
            _ = shutdown_signal(&mut shutdown) => false,
            result = self.accept_tx.send(pending) => result.is_ok(),
        }
    }
}

/// Resolve once the server has been asked to stop.
pub async fn shutdown_signal(rx: &mut watch::Receiver<bool>) {
    loop {
        if *rx.borrow_and_update() {
            return;
        }
        if rx.changed().await.is_err() {
            return;
        }
    }
}

async fn dispatch(
    state: Arc<ServerState>,
    request: Request<Incoming>,
    peer: Option<SocketAddr>,
    local: Option<SocketAddr>,
) -> Result<Response<ServerBody>, std::convert::Infallible> {
    if state.is_shutting_down() {
        return Ok(simple_response(
            StatusCode::SERVICE_UNAVAILABLE,
            "Server is shutting down",
        ));
    }

    let response = if websocket::is_upgrade_request(&request) {
        websocket::handle(state, request, peer, local).await
    } else {
        http_handler::handle(state, request, peer, local).await
    };

    Ok(response.unwrap_or_else(|| {
        simple_response(StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error")
    }))
}

async fn serve_connection(
    state: Arc<ServerState>,
    stream: TcpStream,
    peer: Option<SocketAddr>,
    local: Option<SocketAddr>,
) {
    // Small writes dominate API traffic; Nagle only adds latency.
    let _ = stream.set_nodelay(true);

    let io = TokioIo::new(stream);
    let service = service_fn(move |request: Request<Incoming>| {
        let state = state.clone();
        async move { dispatch(state, request, peer, local).await }
    });

    // `with_upgrades()` is what makes the websocket handshake possible.
    let connection = hyper::server::conn::http1::Builder::new()
        .keep_alive(true)
        .serve_connection(io, service)
        .with_upgrades();

    if let Err(error) = connection.await {
        // Clients hanging up mid-request is routine, not worth surfacing.
        log_debug(&format!("connection error: {error}"));
    }
}

fn log_debug(message: &str) {
    if std::env::var_os("PANTHER_SERVER_DEBUG").is_some() {
        eprintln!("[panther-server] {message}");
    }
}

async fn accept_loop(state: Arc<ServerState>, listener: TcpListener) {
    let local = listener.local_addr().ok();
    let mut shutdown = state.shutdown_rx.clone();

    loop {
        let accepted = tokio::select! {
            biased;
            _ = shutdown_signal(&mut shutdown) => break,
            accepted = listener.accept() => accepted,
        };

        match accepted {
            Ok((stream, peer)) => {
                let state = state.clone();
                state.active_connections.fetch_add(1, Ordering::Relaxed);
                tokio::spawn(async move {
                    let counter = state.clone();
                    serve_connection(state, stream, Some(peer), local).await;
                    counter.active_connections.fetch_sub(1, Ordering::Relaxed);
                });
            }
            Err(error) => {
                // Per-connection errors (EMFILE, connection reset during accept)
                // must not take the listener down.
                log_debug(&format!("accept error: {error}"));
                tokio::time::sleep(std::time::Duration::from_millis(5)).await;
            }
        }
    }
}

/// The Python-facing server.
///
/// Deliberately thin: it binds the socket, runs hyper on tokio, and hands each
/// connection to Python through `accept()`. Driving the ASGI application stays
/// on the Python side, so every call into the interpreter originates on the
/// event loop thread.
#[pyclass(module = "panther_server")]
pub struct Server {
    state: Arc<ServerState>,
    accept_rx: Arc<AsyncMutex<mpsc::Receiver<PendingConnection>>>,
    host: String,
    port: u16,
}

#[pymethods]
impl Server {
    /// `backlog` bounds how many accepted-but-not-yet-handed-to-Python
    /// connections may queue up; `message_buffer` is the per-connection ASGI
    /// message queue depth in each direction. Both exist to bound memory.
    #[new]
    #[pyo3(signature = (host = "127.0.0.1", port = 8000, *, root_path = "", backlog = 1024, message_buffer = 32))]
    fn new(
        host: &str,
        port: u16,
        root_path: &str,
        backlog: usize,
        message_buffer: usize,
    ) -> PyResult<Self> {
        if backlog == 0 || message_buffer == 0 {
            return Err(PyRuntimeError::new_err(
                "`backlog` and `message_buffer` must be greater than zero",
            ));
        }

        // No-op when `configure_runtime()` already ran; this only covers callers
        // that construct a `Server` directly.
        crate::ensure_runtime(None, "panther-server");

        let (accept_tx, accept_rx) = mpsc::channel(backlog);
        let (shutdown_tx, shutdown_rx) = watch::channel(false);

        Ok(Server {
            state: Arc::new(ServerState {
                root_path: root_path.to_string(),
                accept_tx,
                message_buffer,
                local_addr: StdMutex::new(None),
                shutdown_tx,
                shutdown_rx,
                active_connections: AtomicU64::new(0),
            }),
            accept_rx: Arc::new(AsyncMutex::new(accept_rx)),
            host: host.to_string(),
            port,
        })
    }

    /// Bind the socket and start accepting. Resolves as soon as the listener is
    /// bound, so a port conflict raises before the application reports "ready".
    fn start<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let state = self.state.clone();
        let address = format!("{}:{}", self.host, self.port);

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let listener = bind(&address)
                .await
                .map_err(|error| PyOSError::new_err(format!("cannot bind {address}: {error}")))?;
            let local = listener
                .local_addr()
                .map_err(|error| PyOSError::new_err(error.to_string()))?;

            *state.local_addr.lock().expect("local_addr mutex poisoned") = Some(local);

            tokio::spawn(accept_loop(state.clone(), listener));
            Ok((local.ip().to_string(), local.port()))
        })
    }

    /// Await the next connection. Resolves to `None` once the server stops.
    fn accept<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let accept_rx = self.accept_rx.clone();
        let mut shutdown = self.state.shutdown_rx.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let pending = {
                let mut guard = accept_rx.lock().await;
                tokio::select! {
                    biased;
                    pending = guard.recv() => pending,
                    _ = shutdown_signal(&mut shutdown) => None,
                }
            };

            let Some(pending) = pending else {
                return Ok(None::<Py<PyAny>>);
            };

            Python::attach(|py| {
                let connection = Connection::from_pending(py, pending)?;
                Ok(Some(Py::new(py, connection)?.into_any()))
            })
        })
    }

    /// Stop accepting new connections and unblock any pending `accept()`.
    fn shutdown<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let state = self.state.clone();
        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let _ = state.shutdown_tx.send(true);
            Ok(())
        })
    }

    #[getter]
    fn address(&self) -> Option<(String, u16)> {
        self.state
            .local_addr
            .lock()
            .ok()
            .and_then(|guard| *guard)
            .map(|addr| (addr.ip().to_string(), addr.port()))
    }

    #[getter]
    fn active_connections(&self) -> u64 {
        self.state.active_connections.load(Ordering::Relaxed)
    }

    fn __repr__(&self) -> String {
        format!("<panther_server.Server {}:{}>", self.host, self.port)
    }
}

async fn bind(address: &str) -> std::io::Result<TcpListener> {
    TcpListener::bind(address).await
}
