from time import perf_counter

from bson import ObjectId
from bson.errors import InvalidId

from panther.configs import config
from panther.logger import logger


def query_logger(func):
    def log(*args, **kwargs):
        if config['debug'] is False:
            return func(*args, **kwargs)
        start = perf_counter()
        response = func(*args, **kwargs)
        end = perf_counter()
        class_name = args[0].__name__ if hasattr(args[0], '__name__') else args[0].__class__.__name__
        logger.info(f'\033[1mQuery -->\033[0m  {class_name}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log


def clean_object_id(_id: ObjectId | str) -> ObjectId:
    if isinstance(_id, ObjectId):
        return _id
    try:
        return ObjectId(_id)
    except InvalidId:
        raise


def clean_object_id_in_dicts(*args):
    for d in args:
        if d is None:
            continue
        if '_id' in d:
            d['_id'] = clean_object_id(d['_id'])
        if 'id' in d:
            d['id'] = clean_object_id(d['id'])


def merge_dicts(data: dict | None, kwargs: dict | None) -> dict:
    return (data or {}) | (kwargs or {})
