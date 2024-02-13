import logging
import operator
from functools import reduce
from time import perf_counter

from panther.configs import config

try:
    # Only required if user wants to use mongodb
    import bson
except ImportError:
    pass


logger = logging.getLogger('query')


def log_query(func):
    async def log(*args, **kwargs):
        if config['log_queries'] is False:
            return await func(*args, **kwargs)
        start = perf_counter()
        response = await func(*args, **kwargs)
        end = perf_counter()
        class_name = args[0].__name__ if hasattr(args[0], '__name__') else args[0].__class__.__name__
        logger.info(f'\033[1mQuery -->\033[0m  {class_name}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log


def check_connection(func):
    async def wrapper(*args, **kwargs):
        if config['query_engine'] is None:
            msg = "You don't have active database connection, Check your middlewares"
            raise NotImplementedError(msg)
        return await func(*args, **kwargs)
    return wrapper


def prepare_id_for_query(*args, is_mongo: bool = False):
    for d in args:
        if d is None:
            continue
        if 'id' in d:
            d['_id'] = d.pop('id')

        if '_id' in d:
            _converter = _convert_to_object_id if is_mongo else str
            d['_id'] = _converter(d['_id'])


def _convert_to_object_id(_id):
    if isinstance(_id, bson.ObjectId):
        return _id
    try:
        return bson.ObjectId(_id)
    except bson.objectid.InvalidId:
        msg = f'id={_id} is invalid bson.ObjectId'
        raise bson.errors.InvalidId(msg)


def merge_dicts(*args) -> dict:
    return reduce(operator.ior, filter(None, args), {})
