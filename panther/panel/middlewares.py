from panther.middlewares import HTTPMiddleware
from panther.request import Request
from panther.response import RedirectResponse


class RedirectToSlashMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request):
        if not request.path.endswith('/'):
            return RedirectResponse(request.path + '/')
        return await self.dispatch(request=request)
