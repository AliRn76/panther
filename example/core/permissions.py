from panther.permissions import BasePermission
from panther.request import Request


class UserPermission(BasePermission):
    async def __call__(self, request: Request) -> bool:
        if request.user.username == 'Ali':
            return True
        return False
