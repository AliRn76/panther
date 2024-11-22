from datetime import datetime, timedelta

from panther import Panther, status, version
from panther.app import API
from panther.request import Request
from panther.response import Response
from panther.throttling import Throttling
from panther.openapi.urls import urls as openapi_urls


InfoThrottling = Throttling(rate=5, duration=timedelta(minutes=1))


@API()
async def hello_world():
    return {'detail': 'Hello World'}


@API(cache=True, throttling=InfoThrottling)
async def info(request: Request):
    data = {
        'panther_version': version(),
        'datetime_now': datetime.now().isoformat(),
        'user_agent': request.headers.user_agent,
    }
    return Response(data=data, status_code=status.HTTP_202_ACCEPTED)


url_routing = {
    '': hello_world,
    'info': info,
    'swagger': openapi_urls
}

app = Panther(__name__, configs=__name__, urls=url_routing)
