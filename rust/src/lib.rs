//! A Rust ASGI web server for Panther, built on hyper + tokio and exposed to
//! Python through PyO3.
//!
//! Division of labour: Rust owns the socket, HTTP/1.1 parsing and the websocket
//! framing; Python owns the ASGI application. Rust never calls into the
//! interpreter on its own — it publishes connections onto a queue that the
//! asyncio event loop drains via `Server.accept()`, so every entry into Python
//! happens on the loop thread. That keeps the GIL out of the hot path and
//! avoids the cross-thread coroutine scheduling that makes these bridges
//! fragile.

mod asgi;
mod http_handler;
mod server;
mod websocket;

use std::sync::Once;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

static RUNTIME_INIT: Once = Once::new();

/// Configure the tokio runtime backing the server.
///
/// Must be called before the first `Server` is started; later calls are ignored
/// because the runtime can only be built once per process.
#[pyfunction]
#[pyo3(signature = (worker_threads = None, thread_name = "panther-server"))]
fn configure_runtime(worker_threads: Option<usize>, thread_name: &str) -> PyResult<bool> {
    let mut configured = false;
    let name = thread_name.to_string();

    RUNTIME_INIT.call_once(|| {
        let mut builder = tokio::runtime::Builder::new_multi_thread();
        builder.enable_all().thread_name(name);
        if let Some(threads) = worker_threads {
            builder.worker_threads(threads.max(1));
        }
        pyo3_async_runtimes::tokio::init(builder);
        configured = true;
    });

    Ok(configured)
}

/// Number of worker threads tokio would use by default.
#[pyfunction]
fn default_worker_threads() -> PyResult<usize> {
    std::thread::available_parallelism()
        .map(|value| value.get())
        .map_err(|error| PyRuntimeError::new_err(error.to_string()))
}

#[pymodule]
fn _panther_server(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add_class::<server::Server>()?;
    module.add_class::<asgi::Connection>()?;
    module.add_function(wrap_pyfunction!(configure_runtime, module)?)?;
    module.add_function(wrap_pyfunction!(default_worker_threads, module)?)?;
    Ok(())
}
