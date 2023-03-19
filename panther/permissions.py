from panther.request import Request


class BasePermission:
    """
    Just for demonstration
    """
    @classmethod
    def authorization(cls, request: Request) -> bool:
        return True


class AdminPermission:

    @classmethod
    def authorization(cls, request: Request) -> bool:
        return request.user and hasattr(request.user, 'is_admin') and request.user.is_admin
