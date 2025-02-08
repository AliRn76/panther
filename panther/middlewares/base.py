from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class BaseMiddleware:
    """Used in both http & ws requests"""
    async def before(self, request: Request | GenericWebsocket):
        return request

    async def after(self, response: Response | GenericWebsocket):
        return response


class HTTPMiddleware(BaseMiddleware):
    """Used only in http requests"""
    async def before(self, request: Request):
        return request

    async def after(self, response: Response):
        return response


class WebsocketMiddleware(BaseMiddleware):
    """Used only in ws requests"""
    async def before(self, request: GenericWebsocket):
        return request

    async def after(self, response: GenericWebsocket):
        return response
