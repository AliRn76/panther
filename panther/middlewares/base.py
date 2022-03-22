from panther.request import Request
from panther.response import Response


class BaseMiddleware:

    async def before(self, request: Request):
        return request

    async def after(self, response: Response):
        return response
