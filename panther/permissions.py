from panther.request import Request


class BasePermission:

    @classmethod
    def authorization(cls, request: Request) -> bool:
        return True


class AdminPermission(BasePermission):

    @classmethod
    def authorization(cls, request: Request) -> bool:
        return request.user and hasattr(request.user, 'is_admin') and request.user.is_admin
