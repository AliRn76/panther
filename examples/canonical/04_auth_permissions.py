from panther import Panther
from panther.app import API
from panther.exceptions import AuthenticationAPIError
from panther.permissions import BasePermission
from panther.request import Request


class ApiKeyAuthentication:
    async def __call__(self, request: Request) -> dict:
        api_key = request.headers['x-api-key']
        if api_key != 'secret-example-key':
            raise AuthenticationAPIError
        return {'username': 'demo-user', 'is_admin': True}


class IsAdmin(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return bool(request.user and request.user.get('is_admin'))


@API(auth=ApiKeyAuthentication, permissions=[IsAdmin])
async def private_dashboard(request: Request):
    return {
        'message': 'Authenticated request accepted',
        'user': request.user,
    }


url_routing = {
    'private/dashboard/': private_dashboard,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
