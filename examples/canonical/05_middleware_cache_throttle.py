from datetime import timedelta
from time import perf_counter

from panther import Panther
from panther.app import API
from panther.middlewares import HTTPMiddleware
from panther.request import Request
from panther.throttling import Throttle


class TimingHeaderMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request):
        started_at = perf_counter()
        response = await self.dispatch(request=request)
        response.headers['X-Process-Time'] = f'{perf_counter() - started_at:.6f}'
        return response


MIDDLEWARES = [TimingHeaderMiddleware]


@API(cache=timedelta(seconds=10))
async def cached_time():
    return {'cached_for_seconds': 10}


@API(throttling=Throttle(rate=2, duration=timedelta(minutes=1)))
async def limited_endpoint():
    return {'message': 'This endpoint allows two requests per minute per client.'}


url_routing = {
    'cached-time/': cached_time,
    'limited/': limited_endpoint,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
