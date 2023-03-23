import bson
import operator
from functools import reduce
from time import perf_counter

from panther.configs import config
from panther.logger import query_logger


def log_query(func):
    def log(*args, **kwargs):
        if config['log_queries'] is False:
            return func(*args, **kwargs)
        start = perf_counter()
        response = func(*args, **kwargs)
        end = perf_counter()
        class_name = args[0].__name__ if hasattr(args[0], '__name__') else args[0].__class__.__name__
        query_logger.info(f'\033[1mQuery -->\033[0m  {class_name}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log


def clean_object_id(_id: bson.ObjectId | str) -> bson.ObjectId:
    if isinstance(_id, bson.ObjectId):
        return _id
    try:
        return bson.ObjectId(_id)
    except Exception:
        raise bson.errors.InvalidId  # NOQA: Py Unresolved References


def clean_object_id_in_dicts(*args):
    # TODO: Refactor this func
    for d in args:
        if d is None:
            continue
        if '_id' in d:
            d['_id'] = clean_object_id(d['_id'])
        if 'id' in d:
            d['_id'] = clean_object_id(d.pop('id'))


def merge_dicts(*args) -> dict:
    return reduce(operator.ior, filter(None, args), {})
