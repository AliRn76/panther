from panther.configs import config
from panther.logger import logger
from bson import ObjectId, errors
from time import perf_counter


def query_logger(func):
    def log(*args, **kwargs):
        if config['debug'] is False:
            return func(*args, **kwargs)
        start = perf_counter()
        response = func(*args, **kwargs)
        end = perf_counter()
        # logger.info(f'\033[1mQuery -->\033[0m  {args[0].__name__}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        logger.info(f'Query --> {args[0].__name__}.{func.__name__}() --> {(end - start) * 1_000:.2} ms')
        return response
    return log


def to_object_id(_id: str) -> ObjectId:
    if isinstance(_id, ObjectId):
        return _id
    try:
        return ObjectId(_id)
    except errors.InvalidId:
        raise
