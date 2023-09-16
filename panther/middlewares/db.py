from panther.db.connection import DBSession
from panther.middlewares.base import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket


class DatabaseMiddleware(BaseMiddleware):

    def __init__(self, **kwargs):
        self.url = kwargs['url']

    async def before(self, request: Request | GenericWebsocket) -> Request | GenericWebsocket:
        self.db = DBSession(db_url=self.url)
        return request

    async def after(self, response: Response | GenericWebsocket) -> Response | GenericWebsocket:
        self.db.close()
        return response
