import sys

from panther import Panther
from panther.app import API
from panther.exceptions import MethodNotAllowed
from panther.request import Request
from panther.response import Response

URLs = 'main.url_routing'


# Main API
@API()
async def main_api(request: Request, user: int, record: int):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if request.method != 'PUT':
        raise MethodNotAllowed

    if request.headers.authorization is None:
        return Response(data={'detail': 'Authorization Error'}, status_code=401)

    data = {
        'params': {'user': user, 'record': record},
        'query': request.query_params,
        'data': request.pure_data,
    }
    return Response(data=data, status_code=200)


# Fake API
async def fake_api(*args, **kwargs):
    return Response(data={'detail': 'Ok'}, status_code=202)


# Routing
pre_fake_url_routing = dict()
main_url_routing = {'users/<user>/records/<record>': main_api}
post_fake_url_routing = dict()

for n in range(50):
    pre_fake_url_routing['users/<user>/'] = fake_api
    post_fake_url_routing[f'fake-route-{n}/<part>'] = fake_api

url_routing = pre_fake_url_routing | main_url_routing | post_fake_url_routing


app = Panther(__name__, configs=sys.modules[__name__])
