import operator
from functools import reduce
from time import perf_counter

import bson

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


def prepare_id_for_query(*args, is_mongo: bool = False):
    for d in args:
        if d is None:
            continue
        if 'id' in d:
            d['_id'] = d.pop('id')

        if is_mongo and '_id' in d:
            d['_id'] = _convert_to_object_id(d['_id'])


def _convert_to_object_id(_id: bson.ObjectId | str) -> bson.ObjectId:
    if isinstance(_id, bson.ObjectId):
        return _id
    try:
        return bson.ObjectId(_id)
    except bson.objectid.InvalidId:
        raise bson.errors.InvalidId(f'id={_id} is invalid bson.ObjectId')


def merge_dicts(*args) -> dict:
    return reduce(operator.ior, filter(None, args), {})
