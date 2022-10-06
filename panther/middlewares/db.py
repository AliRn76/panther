from panther.logger import logger
from panther.middlewares.base import BaseMiddleware
from panther.db.connection import DBSession
from panther.response import Response
from panther.request import Request


class Middleware(BaseMiddleware):

    def __init__(self, **kwargs):
        self.url = kwargs['url']

    async def before(self, request: Request) -> Request:
        self.db = DBSession(db_url=self.url)
        return request

    async def after(self, response: Response) -> Response:
        self.db.close()
        return response

    @property
    def db_engine(self) -> str:
        return self.url.split(':')[0]

