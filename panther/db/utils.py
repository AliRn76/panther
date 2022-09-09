from panther.configs import config
from panther.logger import logger
from bson import ObjectId, errors
from time import perf_counter
from typing import Union


def query_logger(func):
    def log(*args, **kwargs):
        if config['debug'] is False:
            return func(*args, **kwargs)
        start = perf_counter()
        response = func(*args, **kwargs)
        end = perf_counter()
        class_name = args[0].__name__ if hasattr(args[0], '__name__') else args[0].__class__.__name__
        logger.info(f'\033[1mQuery -->\033[0m  {class_name}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        # logger.info(f'Query --> {class_name}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log


def to_object_id(_id: Union[ObjectId, str]) -> ObjectId:
    if isinstance(_id, ObjectId):
        return _id
    try:
        return ObjectId(_id)
    except errors.InvalidId:
        raise
