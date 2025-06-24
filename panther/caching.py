import logging
from collections import namedtuple
from datetime import datetime, timedelta

import orjson as json

from panther.db.connections import redis
from panther.request import Request
from panther.response import Response
from panther.utils import generate_hash_value_from_string, round_datetime

logger = logging.getLogger('panther')

caches: dict[str, tuple[bytes, dict, int]] = {}
CachedResponse = namedtuple('CachedResponse', ['data', 'headers', 'status_code'])


def api_cache_key(request: Request, duration: timedelta | None = None) -> str:
    client = (request.user and request.user.id) or request.client.ip
    query_params_hash = generate_hash_value_from_string(request.scope['query_string'].decode('utf-8'))
    key = f'{client}-{request.path}-{query_params_hash}-{request.validated_data}'

    if duration:
        time = round_datetime(datetime.now(), duration)
        return f'{time}-{key}'

    return key


async def get_response_from_cache(*, request: Request, duration: timedelta) -> CachedResponse | None:
    """
    If redis.is_connected:
        Get Cached Data From Redis
    else:
        Get Cached Data From Memory
    """
    if redis.is_connected:
        key = api_cache_key(request=request)
        data = (await redis.get(key) or b'{}').decode()
        if value := json.loads(data):
            return CachedResponse(data=value[0].encode(), headers=value[1], status_code=value[2])
    else:
        key = api_cache_key(request=request, duration=duration)
        if value := caches.get(key):
            return CachedResponse(*value)


async def set_response_in_cache(*, request: Request, response: Response, duration: timedelta | int) -> None:
    """
    If redis.is_connected:
        Cache The Data In Redis
    else:
        Cache The Data In Memory
    """

    if redis.is_connected:
        key = api_cache_key(request=request)
        cache_data: tuple[str, dict, int] = (response.body.decode(), response.headers, response.status_code)
        await redis.set(key, json.dumps(cache_data), ex=duration)

    else:
        key = api_cache_key(request=request, duration=duration)
        caches[key] = (response.body, response.headers, response.status_code)
        logger.info('`cache` is not very accurate when `redis` is not connected.')
