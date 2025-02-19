from datetime import datetime, timedelta

from pydantic import BaseModel

from panther import Panther, status, version
from panther.app import API, GenericAPI
from panther.middlewares.base import HTTPMiddleware
from panther.openapi.urls import urls as openapi_urls
from panther.request import Request
from panther.response import Response
from panther.throttling import Throttling

InfoThrottling = Throttling(rate=5, duration=timedelta(minutes=1))


@API()
async def hello_world():
    return {'detail': 'Hello World'}


class TestMiddleware(HTTPMiddleware):
    async def before(self, request: Request):
        return request

    async def after(self, response: Response):
        return response


@API(cache=True, throttling=InfoThrottling, methods=['GET'])
async def info(request: Request):
    data = {
        'panther_version': version(),
        'datetime_now': datetime.now().isoformat(),
        'user_agent': request.headers.user_agent,
    }
    return Response(data=data, status_code=status.HTTP_202_ACCEPTED)


class UserSerializer(BaseModel):
    name: str


class UserAPI(GenericAPI):
    output_model = UserSerializer

    def get(self, *args, **kwargs):
        return


MIDDLEWARES = [TestMiddleware]

url_routing = {
    '': hello_world,
    'info': info,
    'user/': UserAPI,
    'swagger': openapi_urls
}

app = Panther(__name__, configs=__name__, urls=url_routing)
