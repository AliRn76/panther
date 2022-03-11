from bson import ObjectId, errors
import logging


logger = logging.getLogger(__name__)


def to_object_id(_id: str) -> ObjectId:
    if isinstance(_id, ObjectId):
        return _id
    try:
        return ObjectId(_id)
    except errors.InvalidId:
        raise InvalidIdType


def clean_data(data: dict) -> dict:
    for k, v in data.items():
        if k == '_id':
            data[k] = to_object_id(v)
            break
    return data

def query_logger(func):
    def log(*args, **kwargs):
        # TODO: Time Log
        # logger.info(f'\033[1mQuery -->\033[0m {func.__name__}')
        logger.info(f'Query --> {func.__name__}')
        return func(*args, **kwargs)
    return log

