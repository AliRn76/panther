from panther.request import Request


class BasePermission:
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return True


class AdminPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return request.user and getattr(request.user, 'is_admin', False)
