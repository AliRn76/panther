from panther.request import Request
from panther.websocket import Websocket


class BasePermission:
    @classmethod
    async def authorization(cls, request: Request | Websocket) -> bool:
        return True


class AdminPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return request.user and getattr(request.user, 'is_admin', False)
