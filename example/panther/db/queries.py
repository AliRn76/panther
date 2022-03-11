import bson
import logging
from typing import Tuple
from panther.db.connection import db  # It Used In eval
from panther.db.utils import clean_data, query_logger


logger = logging.getLogger(__name__)


class Query:

    # # # Basic
    @classmethod
    @query_logger
    def get_one(cls, **data):
        """ example: \nUser.get_one(_id=_id) """
        _data = clean_data(data)
        return eval(f'db.{cls}.find_one(_data)')

    @classmethod
    @query_logger
    def create(cls, **data) -> bson.objectid.ObjectId:
        """ example: \nUser.create(name='ali', age=24, ...) """
        return eval(f'db.{cls}.insert(data)')

    @classmethod
    @query_logger
    def delete_one(cls, **data):
        """ example: \nUser.delete_one(_id=_id) """
        _data = clean_data(data)
        result = eval(f'db.{cls}.delete_one(_data)')
        return bool(result.deleted_count)

    @classmethod
    @query_logger
    def delete_many(cls, **data) -> int:
        """ example: \nUser.delete_many(name='ali') """
        result = eval(f'db.{cls}.delete_many(data)')
        return result.deleted_count

    @classmethod
    @query_logger
    def update_one(cls, filter, **data) -> dict:
        """ example: \nUser.update_one({'_id': _id}, name='ali') """
        if '_id' in filter:
            filter['_id'] = to_object_id(filter['_id'])
        _update = {'$set': data}
        return eval(f'db.{cls}.update_one(filter, _update)')

    @classmethod
    @query_logger
    def update_many(cls, filter, **data) -> dict:
        """ example: \nUser.update_many({'name': 'mohsen'}, name='ali') """
        _id = filter.get('_id')
        if _id:
            filter['_id'] = to_object_id(_id)
        _update = {'$set': data}
        return eval(f'db.{cls}.update_many(filter, _update)')

    @classmethod
    @query_logger
    def increment(cls, filter, **data):
        """ example: \n    User.increment({'_id': _id}, score=1) \n\t- - it will increment score by 1 """
        _id = filter.get('_id')
        if _id:
            filter['_id'] = to_object_id(_id)
        _update = {'$inc': data}
        return eval(f'db.{cls}.update_one(filter, _update)')

    @classmethod
    @query_logger
    def list(cls, **data):
        """ example: \nUser.list(name='ali', age=24) """
        _data = clean_data(data)
        return eval(f'db.{cls}.find(_data)')

    # # # Advanced
    @classmethod
    @query_logger
    def get_or_create(cls, **data) -> Tuple[bool, any]:
        obj = cls.get_one(**data)
        if obj:
            return False, obj
        else:
            return True, cls.create(**data)

    @classmethod
    @query_logger
    def get_or_raise(cls):
        ...
