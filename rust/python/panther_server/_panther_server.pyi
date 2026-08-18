from collections.abc import Awaitable
from typing import Any, Literal

__version__: str

class Connection:
    """One HTTP request or one websocket session, as ASGI primitives."""

    scope: dict[str, Any]
    kind: Literal['http', 'websocket']

    def receive(self) -> Awaitable[dict[str, Any]]: ...
    def send(self, message: dict[str, Any]) -> Awaitable[None]: ...

class Server:
    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 8000,
        *,
        root_path: str = '',
        backlog: int = 1024,
        message_buffer: int = 32,
    ) -> None: ...

    address: tuple[str, int] | None
    active_connections: int

    def start(self) -> Awaitable[tuple[str, int]]: ...
    def accept(self) -> Awaitable[Connection | None]: ...
    def shutdown(self) -> Awaitable[None]: ...

def configure_runtime(worker_threads: int | None = None, thread_name: str = 'panther-server') -> bool: ...
def default_worker_threads() -> int: ...
