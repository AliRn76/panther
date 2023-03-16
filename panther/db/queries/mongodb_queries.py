from typing import Self

from panther.db.connection import db  # NOQA: F401
from panther.exceptions import DBException
from panther.db.utils import clean_object_id_in_dicts, merge_dicts


class BaseMongoDBQuery:

    @classmethod
    def _merge(cls, *args) -> dict:
        clean_object_id_in_dicts(*args)
        # TODO: Convert "id" to "_id"
        return merge_dicts(*args)

    # # # # # Find # # # # #
    @classmethod
    def find_one(cls, _data: dict = None, /, **kwargs) -> Self | None:
        _query = cls._merge(_data, kwargs)
        if document := eval(f'db.session.{cls.__name__}.find_one(_query)'):
            return cls(**document)

    @classmethod
    def find(cls, _data: dict = None, /, **kwargs) -> list[Self]:
        _query = cls._merge(_data, kwargs)
        documents = eval(f'db.session.{cls.__name__}.find(_query)')
        return [cls(**document) for document in documents]

    # # # # # Insert # # # # #
    @classmethod
    def insert_one(cls, _data: dict = None, **kwargs) -> Self:
        document = cls._merge(_data, kwargs)
        document['id'] = eval(f'db.session.{cls.__name__}.insert_one(document)').inserted_id
        return cls(**document)

    @classmethod
    def insert_many(cls, _data: dict = None, **kwargs) -> Self:
        raise DBException('insert_many() is not supported while using MongoDB.')

    # # # # # Delete # # # # #
    def delete(self) -> None:
        _filter = {'_id': self._id}
        eval(f'db.session.{self.__class__.__name__}.delete_one(_filter)')

    @classmethod
    def delete_one(cls, _data: dict = None, /, **kwargs) -> bool:
        _query = cls._merge(_data, kwargs)
        result = eval(f'db.session.{cls.__name__}.delete_one(_query)')
        return bool(result.deleted_count)

    @classmethod
    def delete_many(cls, _data: dict = None, /, **kwargs) -> int:
        _query = cls._merge(_data, kwargs)
        result = eval(f'db.session.{cls.__name__}.delete_many(_query)')
        return result.deleted_count

    # # # # # Update # # # # #
    def update(self, **kwargs) -> None:
        for field, value in kwargs.items():
            setattr(self, field, value)
        _filter = {'_id': self._id}
        _update = {'$set': kwargs}
        eval(f'db.session.{self.__class__.__name__}.update_one(_filter, _update)')

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> bool:
        clean_object_id_in_dicts(_filter)
        _update = {'$set': kwargs | {}}
        if isinstance(_data, dict):
            _data['$set'] = _data.get('$set', {}) | (kwargs or {})

        result = eval(f'db.session.{cls.__name__}.update_one(_filter, _data | _update)')
        return bool(result.updated_count)

    @classmethod
    def update_many(cls, _filter, _data: dict = None, /, **kwargs) -> int:
        _update = {'$set': cls._merge(_data, kwargs)}
        result = eval(f'db.session.{cls.__name__}.update_many(_filter, _update)')
        return result.updated_count

    # # # # # Other # # # # #
    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        _query = cls._merge(_data, kwargs)
        return eval(f'db.session.{cls.__name__}.count_documents(_query)')
