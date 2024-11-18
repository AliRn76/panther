from collections import namedtuple
from datetime import timedelta, datetime
import logging
from types import NoneType

import orjson as json

from panther.configs import config
from panther.db.connections import redis
from panther.request import Request
from panther.response import Response
from panther.throttling import throttling_storage
from panther.utils import generate_hash_value_from_string, round_datetime

logger = logging.getLogger('panther')

caches = {}
CachedResponse = namedtuple('CachedResponse', ['data', 'headers', 'status_code'])


def api_cache_key(request: Request, cache_exp_time: timedelta | None = None) -> str:
    client = request.user and request.user.id or request.client.ip
    query_params_hash = generate_hash_value_from_string(request.scope['query_string'].decode('utf-8'))
    key = f'{client}-{request.path}-{query_params_hash}-{request.validated_data}'

    if cache_exp_time:
        time = round_datetime(datetime.now(), cache_exp_time)
        return f'{time}-{key}'

    return key


def throttling_cache_key(request: Request, duration: timedelta) -> str:
    client = request.user and request.user.id or request.client.ip
    time = round_datetime(datetime.now(), duration)
    return f'{time}-{client}-{request.path}'


async def get_response_from_cache(*, request: Request, cache_exp_time: timedelta) -> CachedResponse | None:
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
            return CachedResponse(
                data=value[0].encode(),
                headers=value[1],
                status_code=value[2]
            )
    else:
        key = api_cache_key(request=request, cache_exp_time=cache_exp_time)
        if value := caches.get(key):
            return CachedResponse(*value)


async def set_response_in_cache(*, request: Request, response: Response, cache_exp_time: timedelta | int) -> None:
    """
    If redis.is_connected:
        Cache The Data In Redis
    else:
        Cache The Data In Memory
    """

    if redis.is_connected:
        key = api_cache_key(request=request)
        cache_data: tuple[str, str, int] = (response.body.decode(), response.headers, response.status_code)
        cache_exp_time = cache_exp_time or config.DEFAULT_CACHE_EXP
        cache_data: bytes = json.dumps(cache_data)

        if not isinstance(cache_exp_time, timedelta | int | NoneType):
            msg = '`cache_exp_time` should be instance of `datetime.timedelta`, `int` or `None`'
            raise TypeError(msg)

        if cache_exp_time is None:
            logger.warning(
                'your response are going to cache in redis forever '
                '** set DEFAULT_CACHE_EXP in `configs` or set the `cache_exp_time` in `@API.get()` to prevent this **'
            )
            await redis.set(key, cache_data)
        else:
            await redis.set(key, cache_data, ex=cache_exp_time)

    else:
        key = api_cache_key(request=request, cache_exp_time=cache_exp_time)
        cache_data: tuple[bytes, str, int] = (response.body, response.headers, response.status_code)

        caches[key] = cache_data

        if cache_exp_time:
            logger.info('`cache_exp_time` is not very accurate when `redis` is not connected.')


async def get_throttling_from_cache(request: Request, duration: timedelta) -> int:
    """
    If redis.is_connected:
        Get Cached Data From Redis
    else:
        Get Cached Data From Memory
    """
    key = throttling_cache_key(request=request, duration=duration)

    if redis.is_connected:
        data = (await redis.get(key) or b'0').decode()
        return json.loads(data)

    else:
        return throttling_storage[key]


async def increment_throttling_in_cache(request: Request, duration: timedelta) -> None:
    """
    If redis.is_connected:
        Increment The Data In Redis
    else:
        Increment The Data In Memory
    """
    key = throttling_cache_key(request=request, duration=duration)

    if redis.is_connected:
        await redis.incrby(key, amount=1)

    else:
        throttling_storage[key] += 1
