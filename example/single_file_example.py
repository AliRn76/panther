from datetime import datetime, timedelta

from pydantic import BaseModel

from panther import Panther, status, version
from panther.app import API, GenericAPI
from panther.middlewares.base import HTTPMiddleware
from panther.openapi import OutputSchema
from panther.openapi.urls import urls as openapi_urls
from panther.request import Request
from panther.response import Response
from panther.throttling import Throttle

InfoThrottle = Throttle(rate=5, duration=timedelta(minutes=1))


@API()
async def hello_world():
    return {'detail': 'Hello World'}


class TestMiddleware(HTTPMiddleware):
    async def before(self, request: Request):
        return request

    async def after(self, response: Response):
        return response


class UserSerializer(BaseModel):
    name: str = "hi"


@API(throttling=InfoThrottle, input_model=UserSerializer, methods=['GET', 'POST', 'delete'])
async def info(request: Request):
    """Hi from info"""
    data = {
        'panther_version': version(),
        'datetime_now': datetime.now().isoformat(),
        'user_agent': request.headers.user_agent,
    }
    return Response(data=data, status_code=status.HTTP_202_ACCEPTED)

class UserAPI(GenericAPI):
    """Hi from UserAPI"""
    input_model = UserSerializer
    output_schema = OutputSchema(model=UserSerializer, status_code=status.HTTP_205_RESET_CONTENT)

    def get(self, *args, **kwargs):
        return Response({'name': 'ali'}, status.HTTP_202_ACCEPTED)

    def post(self, *args, **kwargs):
        return Response({'name': 'akbar'}, status_code=201)

    async def patch(self, *args, **kwargs):
        data = {'name': 'akbar'}
        status_code = status.HTTP_302_FOUND
        return Response(data=data, status_code=status_code)

    def delete(self, *args, **kwargs):
        data = {'name': 'akbar'}
        status_code = 200
        return Response(data=data, status_code=status_code)


MIDDLEWARES = [TestMiddleware]

url_routing = {
    '': hello_world,
    'info': info,
    'user/': UserAPI,
    'swagger': openapi_urls
}

app = Panther(__name__, configs=__name__, urls=url_routing)
