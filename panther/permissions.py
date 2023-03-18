from panther.request import Request


class BasePermission:

    @classmethod
    def authorization(cls, request: Request) -> bool:
        return True
