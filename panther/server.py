"""Run an ASGI application on the Rust (hyper + tokio) web server.

The Rust extension is optional: it ships as the separate `panther-server`
distribution built from the `rust/` directory of this repository. Everything
here degrades to a clear error message when it is not installed, so importing
`panther.server` is always safe.

    from panther.server import run

    run(app, host='127.0.0.1', port=8000)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from collections.abc import Callable
from typing import Any

from panther._utils import traceback_message
from panther.exceptions import PantherError

logger = logging.getLogger('panther')

__all__ = [
    'ASGIApp',
    'LifespanCycle',
    'available',
    'load_extension',
    'run',
    'serve',
]

ASGIApp = Callable[[dict, Callable, Callable], Any]

INSTALL_HINT = (
    'The Rust web server is not installed.\n'
    '       * Install it with `pip install panther[rust]`\n'
    '       * Or build it from a checkout with `maturin develop --release -m rust/Cargo.toml`'
)


def load_extension():
    """Import the compiled extension, or raise a `PantherError` explaining how to get it."""
    try:
        import panther_server
    except ImportError as exception:
        raise PantherError(INSTALL_HINT) from exception
    return panther_server


def available() -> bool:
    """Whether the Rust web server can be used in this environment."""
    try:
        load_extension()
    except PantherError:
        return False
    return True


class LifespanCycle:
    """Drive the ASGI lifespan protocol for the duration of the server.

    The application's lifespan call is a single long-lived coroutine, so it runs
    as a background task while messages are handed to it through a queue.
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self.queue: asyncio.Queue = asyncio.Queue()
        self.startup_complete = asyncio.Event()
        self.shutdown_complete = asyncio.Event()
        self.error: str | None = None
        self.supported = True
        self.task: asyncio.Future | None = None

    async def _receive(self) -> dict:
        return await self.queue.get()

    async def _send(self, message: dict) -> None:
        message_type = message['type']
        if message_type == 'lifespan.startup.complete':
            self.startup_complete.set()
        elif message_type == 'lifespan.startup.failed':
            self.error = message.get('message', '')
            self.startup_complete.set()
        elif message_type == 'lifespan.shutdown.complete':
            self.shutdown_complete.set()
        elif message_type == 'lifespan.shutdown.failed':
            self.error = message.get('message', '')
            self.shutdown_complete.set()

    async def _main(self) -> None:
        scope = {
            'type': 'lifespan',
            'asgi': {'version': '3.0', 'spec_version': '2.3'},
            'state': {},
        }
        try:
            await self.app(scope, self._receive, self._send)
        except BaseException as exception:  # noqa: BLE001 - reported, not swallowed
            # An app that does not implement lifespan simply raises; that is
            # allowed by the spec and must not stop the server from starting.
            self.supported = False
            self.error = self.error or traceback_message(exception=exception)
        finally:
            self.startup_complete.set()
            self.shutdown_complete.set()

    async def startup(self) -> None:
        self.task = asyncio.ensure_future(self._main())
        await self.queue.put({'type': 'lifespan.startup'})
        await self.startup_complete.wait()

        if self.supported is False:
            logger.debug(f'Lifespan protocol is not supported by the application: {self.error}')
            return
        if self.error is not None:
            raise PantherError(f'Application startup failed: {self.error}')

    async def shutdown(self) -> None:
        if self.task is None or self.supported is False:
            return

        await self.queue.put({'type': 'lifespan.shutdown'})
        await self.shutdown_complete.wait()

        if self.task.done() is False:
            self.task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await self.task

        if self.error is not None:
            logger.error(f'Application shutdown failed: {self.error}')


async def _handle(app: ASGIApp, connection) -> None:
    try:
        await app(connection.scope, connection.receive, connection.send)
    except asyncio.CancelledError:
        raise
    except Exception as exception:  # noqa: BLE001 - a bad endpoint must not kill the server
        logger.error(traceback_message(exception=exception))


async def serve(
    app: ASGIApp,
    host: str = '127.0.0.1',
    port: int = 8000,
    *,
    root_path: str = '',
    workers: int | None = None,
    backlog: int = 1024,
    message_buffer: int = 32,
    lifespan: bool = True,
    graceful_timeout: float = 5.0,
    on_ready: Callable[[str, int], Any] | None = None,
) -> None:
    """Serve `app` until cancelled.

    Args:
        app: Any ASGI 3 application, e.g. a `Panther()` instance.
        host: Interface to bind.
        port: Port to bind; `0` picks a free one, reported through `on_ready`.
        root_path: ASGI `root_path`, for apps mounted under a sub-path.
        workers: tokio worker threads. Defaults to the machine's parallelism.
        backlog: How many accepted connections may wait to be dispatched.
        message_buffer: Per-connection ASGI message queue depth, in each direction.
        lifespan: Run the ASGI lifespan protocol around the server.
        graceful_timeout: Seconds to let in-flight requests finish on shutdown.
        on_ready: Called with the bound `(host, port)` once the socket is listening.

    """
    extension = load_extension()
    extension.configure_runtime(worker_threads=workers)

    lifespan_cycle = LifespanCycle(app) if lifespan else None
    if lifespan_cycle is not None:
        await lifespan_cycle.startup()

    server = extension.Server(
        host,
        port,
        root_path=root_path,
        backlog=backlog,
        message_buffer=message_buffer,
    )
    bound_host, bound_port = await server.start()
    logger.info(f'Panther is running on http://{bound_host}:{bound_port} (rust)')
    if on_ready is not None:
        on_ready(bound_host, bound_port)

    tasks: set[asyncio.Future] = set()
    try:
        while True:
            connection = await server.accept()
            if connection is None:
                break
            task = asyncio.ensure_future(_handle(app, connection))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
    except asyncio.CancelledError:
        pass
    finally:
        await server.shutdown()
        await _drain(tasks, timeout=graceful_timeout)
        if lifespan_cycle is not None:
            await lifespan_cycle.shutdown()


async def _drain(tasks: set[asyncio.Future], timeout: float) -> None:
    """Let in-flight requests finish, then cancel whatever is still running."""
    if not tasks:
        return

    _, pending = await asyncio.wait(set(tasks), timeout=timeout)
    if not pending:
        return

    logger.warning(f'Cancelling {len(pending)} request(s) still running after {timeout}s')
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


def run(
    app: ASGIApp,
    host: str = '127.0.0.1',
    port: int = 8000,
    *,
    root_path: str = '',
    workers: int | None = None,
    backlog: int = 1024,
    message_buffer: int = 32,
    lifespan: bool = True,
    graceful_timeout: float = 5.0,
) -> None:
    """Blocking entry point: run `app` until SIGINT/SIGTERM."""

    async def _main() -> None:
        task = asyncio.ensure_future(
            serve(
                app,
                host=host,
                port=port,
                root_path=root_path,
                workers=workers,
                backlog=backlog,
                message_buffer=message_buffer,
                lifespan=lifespan,
                graceful_timeout=graceful_timeout,
            ),
        )

        loop = asyncio.get_running_loop()
        for signal_name in ('SIGINT', 'SIGTERM'):
            # Not every platform (Windows) supports this; falling back to the
            # default KeyboardInterrupt handling is fine there.
            with contextlib.suppress(AttributeError, NotImplementedError, RuntimeError):
                loop.add_signal_handler(getattr(signal, signal_name), task.cancel)

        with contextlib.suppress(asyncio.CancelledError):
            await task

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_main())
