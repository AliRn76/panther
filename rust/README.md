# panther-server

A Rust web server for [Panther](https://github.com/AliRn76/panther) — [hyper](https://hyper.rs) for
HTTP/1.1 and WebSocket, [tokio](https://tokio.rs) for async I/O, [PyO3](https://pyo3.rs) for the
Python bridge.

This crate builds the optional `panther-server` Python distribution. The application-facing API
lives in `panther.server`; see [the docs](https://pantherpy.github.io/rust_server/).

## Build

```shell
pip install maturin

# Development build, installed into the current environment
maturin develop --release -m rust/Cargo.toml

# Wheel
maturin build --release -m rust/Cargo.toml
```

## Layout

| File               | Responsibility                                                       |
|--------------------|----------------------------------------------------------------------|
| `src/lib.rs`       | Module definition and tokio runtime configuration                     |
| `src/server.rs`    | Listener, connection dispatch, and the Python-facing `Server` object   |
| `src/asgi.rs`      | Scope building, ASGI message conversion, and the `Connection` object   |
| `src/http_handler.rs` | HTTP requests: body pumping and the streaming response body        |
| `src/websocket.rs` | Handshake, upgrade, and frame pumping                                 |

## Design

Rust never calls into Python of its own accord. Each connection becomes an ASGI scope plus a pair of
channels, which are pushed onto a queue; Python drains that queue with `Server.accept()` and drives
the application itself. Every entry into the interpreter therefore happens on the asyncio event loop
thread, which keeps the GIL out of the parsing path and avoids cross-thread coroutine scheduling.

`Connection.receive()` and `Connection.send()` return Python awaitables built with
`pyo3-async-runtimes`; they resolve on the tokio runtime and complete back on the event loop.

## Environment variables

| Name                    | Effect                                       |
|-------------------------|----------------------------------------------|
| `PANTHER_SERVER_DEBUG`  | Print per-connection errors to stderr        |
