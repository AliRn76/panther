from typing import TypeVar

import bson

from panther.db.connection import db  # NOQA: F401
from panther.db.utils import clean_object_id_in_dicts, merge_dicts, log_query

# TODO: Not sure about this bounding
T = TypeVar('T', bound='BaseMongoDBQuery')


class BaseMongoDBQuery:

    @classmethod
    def get_one(cls: type[T], _data: dict = None, /, **kwargs) -> T:
        clean_object_id_in_dicts(_data, kwargs)
        _query = merge_dicts(_data, kwargs)
        obj = eval(f'db.session.{cls.__name__}.find_one(_query)')
        return cls(**obj) if obj else None

    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        clean_object_id_in_dicts(_data, kwargs)
        _query = merge_dicts(_data, kwargs)
        return eval(f'db.session.{cls.__name__}.count_documents(_query)')

    @classmethod
    def list(cls, _data: dict = None, /, **kwargs):
        clean_object_id_in_dicts(_data, kwargs)
        _query = merge_dicts(_data, kwargs)
        result = eval(f'db.session.{cls.__name__}.find(_query)')
        return [cls(**obj) for obj in result]

    @classmethod
    def create(cls, _data: dict = None, **kwargs) -> bson.objectid.ObjectId:
        _query = merge_dicts(_data, kwargs)
        return eval(f'db.session.{cls.__name__}.insert_one(_query)').inserted_id

    def delete(self) -> bool:
        _filter = {'_id': self._id}
        result = eval(f'db.session.{self.__class__.__name__}.delete_one(_filter)')
        return bool(result.deleted_count)

    @classmethod
    def delete_one(cls, **kwargs) -> bool:
        clean_object_id_in_dicts(kwargs)
        result = eval(f'db.session.{cls.__name__}.delete_one(kwargs)')
        return bool(result.deleted_count)

    @classmethod
    def delete_many(cls, **kwargs) -> int:
        clean_object_id_in_dicts(kwargs)
        result = eval(f'db.session.{cls.__name__}.delete_many(kwargs)')
        return result.deleted_count

    def update(self, _data: dict = None, **kwargs) -> dict:
        for field, value in (_data or kwargs).items():
            if hasattr(self, field):
                setattr(self, field, value)
        _filter = {'_id': self._id}
        _update = {'$set': kwargs}
        return eval(f'db.session.{self.__class__.__name__}.update_one(_filter, _update)')

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> dict:
        clean_object_id_in_dicts(_filter)

        _update = {'$set': kwargs | {}}
        if isinstance(_data, dict):
            _data['$set'] = _data.get('$set', {}) | (kwargs or {})

        return eval(f'db.session.{cls.__name__}.update_one(_filter, _data | _update)')

    @classmethod
    def update_many(cls, _filter, **kwargs) -> dict:
        _update = {'$set': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many(_filter, _update)')

    @classmethod
    def increment(cls, _filter, **kwargs):
        _update = {'$inc': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many({_filter}, {_update})')

    @classmethod
    def get_or_create(cls, **kwargs) -> tuple[bool, any]:
        obj = cls.get_one(**kwargs)
        if obj:
            return False, obj
        else:
            return True, cls.create(**kwargs)
