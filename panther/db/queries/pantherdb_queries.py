from __future__ import annotations

from collections.abc import Iterable
from sys import version_info

from pantherdb import Cursor

from panther.db.connections import db
from panther.db.cursor import Cursor
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import prepare_id_for_query
from panther.exceptions import DatabaseError

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BasePantherDBQuery')


class BasePantherDBQuery(BaseQuery):
    @classmethod
    def _merge(cls, *args, is_mongo: bool = False) -> dict:
        return super()._merge(*args, is_mongo=is_mongo)

    # # # # # Find # # # # #
    @classmethod
    async def find_one(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).find_one(**cls._merge(_filter, kwargs)):
            return await cls._create_model_instance(document=document)
        return None

    @classmethod
    async def find(cls, _filter: dict | None = None, /, **kwargs) -> Cursor:
        cursor = db.session.collection(cls.__name__).find(**cls._merge(_filter, kwargs))
        cursor.response_type = cls._create_model_instance
        cursor.cls = cls
        return cursor

    @classmethod
    async def first(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).first(**cls._merge(_filter, kwargs)):
            return await cls._create_model_instance(document=document)
        return None

    @classmethod
    async def last(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).last(**cls._merge(_filter, kwargs)):
            return await cls._create_model_instance(document=document)
        return None

    @classmethod
    async def aggregate(cls, *args, **kwargs):
        msg = 'aggregate() does not supported in `PantherDB`.'
        raise DatabaseError(msg) from None

    # # # # # Count # # # # #
    @classmethod
    async def count(cls, _filter: dict | None = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).count(**cls._merge(_filter, kwargs))

    # # # # # Insert # # # # #
    @classmethod
    async def insert_one(cls, document: dict) -> Self:
        insert_one_result = db.session.collection(cls.__name__).insert_one(**document)
        return insert_one_result['_id']

    @classmethod
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        return [await cls.insert_one(document) for document in documents]

    # # # # # Delete # # # # #
    async def delete(self) -> None:
        db.session.collection(self.__class__.__name__).delete_one(_id=self._id)

    @classmethod
    async def delete_one(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        return db.session.collection(cls.__name__).delete_one(**cls._merge(_filter, kwargs))

    @classmethod
    async def delete_many(cls, _filter: dict | None = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).delete_many(**cls._merge(_filter, kwargs))

    # # # # # Update # # # # #
    async def update(self, _update: dict | None = None, /, **kwargs) -> None:
        document = self._merge(_update, kwargs)
        document.pop('_id', None)
        self._validate_data(data=kwargs, is_updating=True)

        for field, value in document.items():
            if isinstance(value, dict):
                value = type(getattr(self, field))(**value)
            setattr(self, field, value)
        db.session.collection(self.__class__.__name__).update_one({'_id': self._id}, **document)

    @classmethod
    async def update_one(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> bool:
        prepare_id_for_query(_filter)
        return db.session.collection(cls.__name__).update_one(_filter, **cls._merge(_update, kwargs))

    @classmethod
    async def update_many(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> int:
        prepare_id_for_query(_filter)
        return db.session.collection(cls.__name__).update_many(_filter, **cls._merge(_data, kwargs))
