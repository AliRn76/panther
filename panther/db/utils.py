import logging
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
        if config.LOG_QUERIES is False:
            return await func(*args, **kwargs)
        start = perf_counter()
        response = await func(*args, **kwargs)
        end = perf_counter()
        class_name = getattr(args[0], '__name__', args[0].__class__.__name__)
        logger.info(f'[Query] {class_name}.{func.__name__}() takes {(end - start) * 1_000:.3} ms')
        return response

    return log


def check_connection(func):
    async def wrapper(*args, **kwargs):
        if config.QUERY_ENGINE is None:
            msg = (
                "You don't have active database connection, Check your DATABASE block in configs"
                '\nMore Info: https://PantherPy.GitHub.io/database/'
            )
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
    if _id is None:
        return None
    if isinstance(_id, bson.ObjectId):
        return _id
    try:
        return bson.ObjectId(_id)
    except bson.objectid.InvalidId:
        logger.warning(f'id={_id} is not a valid bson.ObjectId')
        return None
