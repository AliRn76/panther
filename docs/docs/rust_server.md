# Rust Web Server

Panther can run on a web server written in Rust — [hyper](https://hyper.rs) for HTTP/1.1,
[tokio](https://tokio.rs) for async I/O, and [PyO3](https://pyo3.rs) for the bridge back into Python.

It is **opt-in**. `uvicorn` remains the default, so nothing changes unless you ask for it.

## Installation

```shell
pip install panther[rust]
```

Or build it from a checkout of the repository (needs a [Rust toolchain](https://rustup.rs)):

```shell
pip install maturin
maturin develop --release -m rust/Cargo.toml
```

## Usage

### From the CLI

```shell
panther run --server rust main:app
```

Options:

| Option          | Default     | Description                                        |
|-----------------|-------------|----------------------------------------------------|
| `--host`        | `127.0.0.1` | Interface to bind                                  |
| `--port`        | `8000`      | Port to bind; `0` picks a free one                 |
| `--workers`     | *CPU count* | Number of tokio worker threads                     |
| `--root-path`   | `''`        | ASGI `root_path` for apps mounted under a sub-path |
| `--no-lifespan` | *off*       | Skip the ASGI lifespan protocol                    |

!!! note
    These are the options the Rust server understands. Uvicorn-only flags such as `--reload`
    are rejected rather than silently ignored, so run `panther run main:app --reload` in
    development and switch to `--server rust` when you want the throughput.

### From Python

```python
from panther import Panther
from panther.server import run

app = Panther(__name__)

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8000, workers=4)
```

`panther.server.serve()` is the coroutine underneath, for when you already own the event loop:

```python
import asyncio
from panther.server import serve

asyncio.run(serve(app, port=8000))
```

Check availability before committing to it:

```python
from panther.server import available

if available():
    ...
```

### A runnable example

`examples/canonical/11_rust_server.py` is a complete app with HTTP and WebSocket endpoints:

```shell
panther run --server rust examples.canonical.11_rust_server:app

# or, using the `run()` call at the bottom of that file
python -m examples.canonical.11_rust_server
```

## What it supports

- HTTP/1.1 with keep-alive, request streaming and response streaming
- WebSocket (RFC 6455), including subprotocol negotiation and denial responses
- The ASGI lifespan protocol, so `startup`/`shutdown` events and database connections behave as usual

Anything that speaks ASGI 3 works — the server is not Panther-specific.

## How it works

Rust owns the socket, the HTTP parsing and the websocket framing. Python owns the application.

The two halves meet at a queue: hyper turns each connection into an ASGI `scope` plus a pair of
channels, pushes it onto that queue, and the asyncio event loop drains it with `Server.accept()`.
Your application is then driven from Python exactly as any ASGI server would, with `receive` and
`send` backed by the Rust channels.

The important consequence is that **Rust never calls into the interpreter on its own**. Every entry
into Python happens on the event loop thread, which keeps the GIL out of the parsing hot path and
avoids the cross-thread coroutine scheduling that makes these bridges fragile.

## Limitations

- HTTP/2 and HTTP/3 are not implemented yet; HTTP/1.1 only.
- No TLS termination — put it behind nginx, Caddy or a load balancer, as you would uvicorn.
- No `--reload`. Use uvicorn during development.
- Multi-process (`--workers` in the uvicorn sense) is not handled here; `--workers` sets tokio
  threads inside one process. Use a process manager or Gunicorn-style preforking if you need more.

## Building wheels

```shell
maturin build --release -m rust/Cargo.toml
```

The crate lives in `rust/` and builds a separate `panther-server` distribution, so a plain
`pip install panther` never requires a Rust toolchain.
