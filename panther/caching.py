from collections import namedtuple
from datetime import timedelta, datetime
import logging
from types import NoneType

import orjson as json

from panther.configs import config
from panther.db.connection import redis
from panther.request import Request
from panther.response import Response, ResponseDataTypes
from panther.utils import generate_hash_value_from_string, round_datetime

logger = logging.getLogger('panther')

caches = {}
CachedResponse = namedtuple('Cached', ['data', 'status_code'])


def cache_key(request: Request, /) -> str:
    client = request.user and request.user.id or request.client.ip
    query_params_hash = generate_hash_value_from_string(request.scope['query_string'].decode('utf-8'))
    return f'{client}-{request.path}-{query_params_hash}-{request.validated_data}'


def local_cache_key(*, request: Request, cache_exp_time: timedelta | None = None) -> str:
    key = cache_key(request)
    if cache_exp_time:
        time = round_datetime(datetime.now(), cache_exp_time)
        return f'{time}-{key}'
    else:
        return key


def get_cached_response_data(*, request: Request, cache_exp_time: timedelta) -> CachedResponse | None:
    """
    If redis.is_connected:
        Get Cached Data From Redis
    else:
        Get Cached Data From Memory
    """
    if redis.is_connected:  # noqa: Unresolved References
        key = cache_key(request)
        data = (redis.get(key) or b'{}').decode()
        if cached_value := json.loads(data):
            return CachedResponse(*cached_value)

    else:
        key = local_cache_key(request=request, cache_exp_time=cache_exp_time)
        if cached_value := caches.get(key):
            return CachedResponse(*cached_value)

    return None


def set_cache_response(*, request: Request, response: Response, cache_exp_time: timedelta | int) -> None:
    """
    If redis.is_connected:
        Cache The Data In Redis
    else:
        Cache The Data In Memory
    """

    cache_data: tuple[ResponseDataTypes, int] = (response.data, response.status_code)

    if redis.is_connected:  # noqa: Unresolved References
        key = cache_key(request)

        cache_exp_time = cache_exp_time or config['default_cache_exp']
        cache_data: bytes = json.dumps(cache_data)

        if not isinstance(cache_exp_time, timedelta | int | NoneType):
            msg = '"cache_exp_time" should be instance of "datetime.timedelta" or "int" or "None"'
            raise TypeError(msg)

        if cache_exp_time is None:
            logger.warning(
                'your response are going to cache in redis forever '
                '** set DEFAULT_CACHE_EXP in configs or pass the cache_exp_time in @API.get() for prevent this **'
            )
            redis.set(key, cache_data)
        else:
            redis.set(key, cache_data, ex=cache_exp_time)

    else:
        key = local_cache_key(request=request, cache_exp_time=cache_exp_time)
        caches[key] = cache_data

        if cache_exp_time:
            logger.info('"cache_exp_time" is not very accurate when redis is not connected.')
