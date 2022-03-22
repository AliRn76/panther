from panther.middlewares.base import BaseMiddleware
from panther.db.connection import DBSession
from panther.response import Response
from panther.request import Request


class Middleware(BaseMiddleware):

    async def before(self, request: Request):
        self.db = DBSession(db_url=request.db_url)
        return request

    async def after(self, response: Response):
        self.db.session.close()
        return response


