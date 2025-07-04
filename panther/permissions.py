from abc import abstractmethod

from panther.request import Request
from panther.websocket import Websocket


class BasePermission:
    @abstractmethod
    async def __call__(self, request: Request | Websocket) -> bool:
        return True


class IsAdmin(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return request.user and getattr(request.user, 'is_admin', False)


class IsAuthenticatedOrReadonly(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return request.user or request.method == 'GET'
