"""Rust (hyper + tokio) ASGI web server for Panther.

This package only exposes the compiled extension. The application-facing entry
point lives in `panther.server`, which knows how to drive an ASGI app with the
primitives defined here.
"""

from panther_server._panther_server import (
    Connection,
    Server,
    __version__,
    configure_runtime,
    default_worker_threads,
)

__all__ = [
    'Connection',
    'Server',
    '__version__',
    'configure_runtime',
    'default_worker_threads',
]
