from panther.exceptions import RedirectAPIError
from panther.permissions import BasePermission
from panther.request import Request


class IsAuthenticated(BasePermission):
    async def __call__(self, request: Request):
        if request.user is None:
            raise RedirectAPIError(url=f'login?redirect_to={request.path}')
