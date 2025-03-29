import typing

from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class BaseMiddleware:
    """Used in both http & ws requests"""

    def __init__(self, dispatch: typing.Callable):
        self.dispatch = dispatch

    async def __call__(self, request: Request | GenericWebsocket) -> Response | GenericWebsocket:
        return await self.dispatch(request=request)


class HTTPMiddleware(BaseMiddleware):
    """Used only in http requests"""

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request=request)


class WebsocketMiddleware(BaseMiddleware):
    """Used only in ws requests"""

    async def __call__(self, request: GenericWebsocket) -> GenericWebsocket:
        return await self.dispatch(request=request)
