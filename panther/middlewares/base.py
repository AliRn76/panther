from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class BaseMiddleware:
    async def before(self, request: Request | GenericWebsocket):
        raise NotImplementedError

    async def after(self, response: Response | GenericWebsocket):
        raise NotImplementedError


class HTTPMiddleware(BaseMiddleware):
    async def before(self, request: Request):
        return request

    async def after(self, response: Response):
        return response


class WebsocketMiddleware(BaseMiddleware):
    async def before(self, request: GenericWebsocket):
        return request

    async def after(self, response: GenericWebsocket):
        return response
