from abc import abstractmethod

from panther.request import Request
from panther.websocket import Websocket


class BasePermission:
    @abstractmethod
    async def __call__(self, request: Request | Websocket) -> bool:
        return True


class IsAuthenticated(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return bool(request.user)


class IsAuthenticatedOrReadonly(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return request.user or request.method == 'GET'
