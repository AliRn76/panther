from panther.permissions import BasePermission
from panther.request import Request


class UserPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        if request.user.username == 'Ali':
            return True
        return False
