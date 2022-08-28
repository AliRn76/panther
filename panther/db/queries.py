import bson
from typing import Tuple
from panther.db.connection import db
from panther.db.utils import query_logger, to_object_id
import datetime  # # # Do Not Delete This Import (Used in eval)
from bson import ObjectId  # # # Do Not Delete This Import (Used in eval)


class MongoQuery:
    # # # Main

    @classmethod
    @query_logger
    def get_one(cls, _data: dict = None, /, **kwargs):
        """
        example:
            User.get_one(id=id)
        """
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
        """
        example:
            User.count({'state': {'$eq': 'Confirmed'}}, name='ali', age=24)
        """
        if _data is None:
            _data = {}

        _data = {k: v for k, v in _data.items() if v not in [None]}
        kwargs = {k: v for k, v in kwargs.items() if v not in [None]}
        if '_id' in _data:
            _data['_id'] = to_object_id(_data['_id'])
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        return eval(f'db.session.{cls.__name__}.count_documents(_data | kwargs)')

    @classmethod
    @query_logger
    def list(cls, _data: dict = None, /, **kwargs):
        """
        example:
            User.list({'state': {'$eq': 'Confirmed'}}, name='ali', age=24)
        """
        if _data is None:
            _data = {}
        _data = {k: v for k, v in _data.items() if v not in [None]}
        kwargs = {k: v for k, v in kwargs.items() if v not in [None]}
        if '_id' in _data:
            _data['_id'] = to_object_id(_data['_id'])
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        return eval(f'db.session.{cls.__name__}.find(_data | kwargs)')

    @classmethod
    @query_logger
    def create(cls, **kwargs) -> bson.objectid.ObjectId:
        """
        example:
            User.create(name='ali', age=24, ...)
        """
        return eval(f'db.session.{cls.__name__}.insert_one({kwargs})').inserted_id

    @query_logger
    def delete(self) -> bool:
        """
        example:
            User.delete()
        """
        _filter = {'_id': self._id}
        result = eval(f'db.session.{self.__class__.__name__}.delete_one(_filter)')
        return bool(result.deleted_count)

    @classmethod
    @query_logger
    def delete_one(cls, **kwargs) -> bool:
        """
        example:
            User.delete_one(id=_id)
        """
        if '_id' in kwargs:
            kwargs['_id'] = to_object_id(kwargs['_id'])
        result = eval(f'db.session.{cls.__name__}.delete_one(_data)')
        return bool(result.deleted_count)

    @classmethod
    @query_logger
    def delete_many(cls, **kwargs) -> int:
        """
        example:
            User.delete_many(name='ali')
        """
        result = eval(f'db.session.{cls.__name__}.delete_many(kwargs)')
        return result.deleted_count

    @query_logger
    def update(self, **kwargs) -> dict:
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        _filter = {'_id': self._id}
        _update = {'$set': kwargs}
        return eval(f'db.session.{self.__class__.__name__}.update_one(_filter, _update)')

    @classmethod
    @query_logger
    def update_one(cls, filter, _data: dict = None, /, **kwargs) -> dict:
        """
        example:
            User.update_one({'id': _id}, name='ali')
        """
        if '_id' in filter:
            filter['_id'] = to_object_id(filter['_id'])
        if _data is None:
            _data = {}
        _data = {k: v for k, v in _data.items() if v is not None}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        _update = {'$set': kwargs}

        return eval(f'db.session.{cls.__name__}.update_one(filter, _data | _update)')

    @classmethod
    @query_logger
    def update_many(cls, filter, **kwargs) -> dict:
        """
        example:
            User.update_many({'name': 'mohsen'}, name='ali')
        """
        _update = {'$set': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many(filter, _update)')

    @classmethod
    @query_logger
    def increment(cls, filter, **kwargs):
        """
        example:
            User.increment({'priority': {'$gt': ad.priority}}, score=1)
        * it will increment score by 1
        """
        _update = {'$inc': kwargs}
        return eval(f'db.session.{cls.__name__}.update_many({filter}, {_update})')

    @classmethod
    @query_logger
    def get_or_create(cls, **kwargs) -> Tuple[bool, any]:
        obj = cls.get_one(**kwargs)
        if obj:
            return False, obj
        else:
            return True, cls.create(**kwargs)


class SQLiteQuery:

    @classmethod
    @query_logger
    def get_one(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs).first()

    @classmethod
    @query_logger
    def create(cls, body: dict = None, *args, **kwargs):
        """ You can pass data as dict & as kwargs """
        if body:
            obj = cls(**body)
        else:
            obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    @query_logger
    def update(self, *args, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        db.session.commit()
        return self

    @classmethod
    @query_logger
    def list(cls, *args, **kwargs):
        return db.session.query(cls).filter_by(**kwargs)

    @classmethod
    @query_logger
    def delete(cls, commit=True, **kwargs) -> bool:
        """ return boolean --> True=Deleted, False=NotFound  """
        objs = cls.list(**kwargs)
        if not objs.first():
            return False
        objs.delete()
        if commit:
            db.session.commit()
        return True

    @classmethod
    @query_logger
    def last(cls, field='id'):
        return db.session.query(cls).order_by(eval(f'cls.{field}.desc()')).first()

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.get_one(**kwargs)
        if obj:
            return obj
        else:
            return cls.create(**kwargs)

