from collections import namedtuple
from datetime import timedelta

import orjson as json

from panther.configs import config
from panther.db.connection import redis
from panther.logger import logger
from panther.request import Request
from panther.response import Response


caches = dict()
Cached = namedtuple('Cached', ['data', 'status_code'])


def cache_key(request: Request, /):
    # TODO: Add request.data and ... to key
    if request.user:
        key = f'{request.user.id}-{request.path}'
    else:
        key = f'{request.client.ip}-{request.path}'
    return key


def get_cached_response_data(*, request: Request) -> Cached | None:
    """
    If redis.is_connected:
        Get Cached Data From Redis
    else:
        Get Cached Data From Memory
    """
    key = cache_key(request)
    # noinspection PyUnresolvedReferences
    if redis.is_connected:
        data = (redis.get(key) or b'{}').decode()
        if cached := json.loads(data):
            return Cached(*cached)
        else:
            return None

    else:
        global caches
        if cached := caches.get(key):
            return Cached(*cached)
        else:
            return None


def set_cache_response(*, request: Request, response: Response, cache_exp_time: timedelta | int) -> None:
    """
    If redis.is_connected:
        Cache The Data In Redis
    else:
        Cache The Data In Memory
    """
    key = cache_key(request)
    cache_data = (response._data, response.status_code)

    # noinspection PyUnresolvedReferences
    if redis.is_connected:
        cache_exp_time = cache_exp_time or config['default_cache_exp']
        cache_data = json.dumps(cache_data)
        if cache_exp_time is None:
            logger.warning(
                'your response are going to cache in redis forever '
                '** set DEFAULT_CACHE_EXP in configs or pass the cache_exp_time in @API.get() for prevent this **'
            )
            redis.set(key, cache_data)
        else:
            redis.set(key, cache_data, ex=cache_exp_time)

    else:
        global caches
        caches[key] = cache_data

        if cache_exp_time:
            logger.error('cache_exp_time not supported while redis is not connected.')
