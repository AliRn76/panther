import bson
from typing import Tuple
from typing import Type, TypeVar
from panther.db.utils import query_logger, to_object_id
from panther.db.connection import db  # # # Do Not Delete This Import (Used in eval)


# TODO: Not sure about this bounding
T = TypeVar('T', bound='BaseMongoDBQuery')


class BaseMongoDBQuery:

    @classmethod
    @query_logger
    def get_one(cls: Type[T], _data: dict = None, /, **kwargs) -> T:
        if _data is None:
            _data = {}
        if '_id' in _data:
            _data['_id'] = to_object_id(_data['_id'])
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        obj = eval(f'db.session.{cls.__name__}.find_one(_data | kwargs)')
        return cls(**obj) if obj else None

    @classmethod
    @query_logger
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        if _data is None:
            _data = {}

        _data = {k: v for k, v in _data.items() if v not in [None]}
        kwargs = {k: v for k, v in kwargs.items() if v not in [None]}
        if '_id' in _data:
            _data['_id'] = to_object_id(_data['_id'])
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        if 'id' in _data:
            _data['_id'] = to_object_id(_data['id'])
        if 'id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['id'])
        return eval(f'db.session.{cls.__name__}.count_documents(_data | kwargs)')

    @classmethod
    @query_logger
    def list(cls, _data: dict = None, /, **kwargs):
        if _data is None:
            _data = {}
        _data = {k: v for k, v in _data.items() if v not in [None]}
        kwargs = {k: v for k, v in kwargs.items() if v not in [None]}
        if '_id' in _data:
            _data['_id'] = to_object_id(_data['_id'])
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        if 'id' in _data:
            _data['_id'] = to_object_id(_data['id'])
        if 'id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['id'])
        result = eval(f'db.session.{cls.__name__}.find(_data | kwargs)')
        return [cls(**obj) for obj in result]

    @classmethod
    @query_logger
    def create(cls, _data: dict = None, **kwargs) -> bson.objectid.ObjectId:
        return eval(f'db.session.{cls.__name__}.insert_one({_data or kwargs})').inserted_id

    @query_logger
    def delete(self) -> bool:
        _filter = {'_id': self._id}
        result = eval(f'db.session.{self.__class__.__name__}.delete_one(_filter)')
        return bool(result.deleted_count)

    @classmethod
    @query_logger
    def delete_one(cls, **kwargs) -> bool:
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        if 'id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['id'])
        result = eval(f'db.session.{cls.__name__}.delete_one(_data)')
        return bool(result.deleted_count)

    @classmethod
    @query_logger
    def delete_many(cls, **kwargs) -> int:
        result = eval(f'db.session.{cls.__name__}.delete_many(kwargs)')
        return result.deleted_count

    @query_logger
    def update(self, _data: dict = None, **kwargs) -> dict:
        for field, value in (_data or kwargs).items():
            if hasattr(self, field):
                setattr(self, field, value)
        _filter = {'_id': self._id}
        _update = {'$set': kwargs}
        return eval(f'db.session.{self.__class__.__name__}.update_one(_filter, _update)')

    @classmethod
    @query_logger
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> dict:
        if '_id' in _filter:
            _filter['_id'] = to_object_id(_filter['_id'])
        if 'id' in _filter:
            _filter['_id'] = to_object_id(_filter['id'])
        if _data is None:
            _data = {}
        _data = {k: v for k, v in _data.items() if v is not None}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        _update = {'$set': kwargs}

        return eval(f'db.session.{cls.__name__}.update_one(_filter, _data | _update)')

    @classmethod
    @query_logger
    def update_many(cls, _filter, **kwargs) -> dict:
        _update = {'$set': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many(_filter, _update)')

    @classmethod
    @query_logger
    def increment(cls, _filter, **kwargs):
        _update = {'$inc': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many({_filter}, {_update})')

    @classmethod
    @query_logger
    def get_or_create(cls, **kwargs) -> Tuple[bool, any]:
        obj = cls.get_one(**kwargs)
        if obj:
            return False, obj
        else:
            return True, cls.create(**kwargs)
