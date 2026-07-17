import typing

from panther.base_websocket import Websocket
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


def compile_middleware_chain(dispatch: typing.Callable, middleware_classes: list[type]) -> typing.Callable:
    for middleware_class in reversed(middleware_classes):
        dispatch = middleware_class(dispatch=dispatch)
    return dispatch


class HTTPMiddleware:
    """Used only in http requests"""

    def __init__(self, dispatch: typing.Callable):
        self.dispatch = dispatch

    async def __call__(self, request: Request) -> Response:
        return await self.dispatch(request=request)


class WebsocketMiddleware:
    """Used only in ws requests"""

    def __init__(self, dispatch: typing.Callable):
        self.dispatch = dispatch

    async def __call__(self, connection: Websocket) -> GenericWebsocket:
        return await self.dispatch(connection=connection)
