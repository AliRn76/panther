from panther.db.connections import DatabaseSession
from panther.middlewares.base import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class DatabaseMiddleware(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket) -> Request | GenericWebsocket:
        self.db = DatabaseSession(init=True)
        return request

    async def after(self, response: Response | GenericWebsocket) -> Response | GenericWebsocket:
        self.db.close()
        return response
