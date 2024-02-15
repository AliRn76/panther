from __future__ import annotations
from sys import version_info
from bson.codec_options import CodecOptions

from panther.db.connections import db
from panther.db.cursor import Cursor
from panther.db.utils import merge_dicts, prepare_id_for_query
from panther.exceptions import DatabaseError


if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseMongoDBQuery')


class BaseMongoDBQuery:
    @classmethod
    def _merge(cls, *args) -> dict:
        prepare_id_for_query(*args, is_mongo=True)
        return merge_dicts(*args)

    @classmethod
    def collection(cls):
        return db.session.get_collection(
            name=cls.__name__,
            codec_options=CodecOptions(document_class=dict)
            # codec_options=CodecOptions(document_class=cls) TODO: https://jira.mongodb.org/browse/PYTHON-4192
        )

    # # # # # Find # # # # #
    @classmethod
    async def find_one(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        if document := await cls.collection().find_one(cls._merge(_data, kwargs)):
            return cls._create_model_instance(document=document)
        return None

    @classmethod
    async def find(cls, _data: dict | None = None, /, **kwargs) -> Cursor:
        return Cursor(cls=cls, collection=cls.collection().delegate, filter=cls._merge(_data, kwargs))

    @classmethod
    async def first(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        return await cls.find_one(_data, **kwargs)

    @classmethod
    async def last(cls, _data: dict | None = None, /, **kwargs):
        msg = 'last() is not supported in MongoDB yet.'
        raise DatabaseError(msg)

    # # # # # Count # # # # #
    @classmethod
    async def count(cls, _data: dict | None = None, /, **kwargs) -> int:
        return await cls.collection().count_documents(cls._merge(_data, kwargs))

    # # # # # Insert # # # # #
    @classmethod
    async def insert_one(cls, _data: dict | None = None, /, **kwargs) -> Self:
        document = cls._merge(_data, kwargs)
        await cls.collection().insert_one(document)
        return cls._create_model_instance(document=document)

    # # # # # Delete # # # # #
    async def delete(self) -> None:
        await self.collection().delete_one({'_id': self._id})

    @classmethod
    async def delete_one(cls, _data: dict | None = None, /, **kwargs) -> bool:
        result = await cls.collection().delete_one(cls._merge(_data, kwargs))
        return bool(result.deleted_count)

    @classmethod
    async def delete_many(cls, _data: dict | None = None, /, **kwargs) -> int:
        result = await cls.collection().delete_many(cls._merge(_data, kwargs))
        return result.deleted_count

    # # # # # Update # # # # #
    async def update(self, **kwargs) -> None:
        for field, value in kwargs.items():
            setattr(self, field, value)
        update_fields = {'$set': kwargs}
        await self.collection().update_one({'_id': self._id}, update_fields)

    @classmethod
    async def update_one(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> bool:
        prepare_id_for_query(_filter, is_mongo=True)
        update_fields = {'$set': cls._merge(_data, kwargs)}

        result = await cls.collection().update_one(_filter, update_fields)
        return bool(result.matched_count)

    @classmethod
    async def update_many(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> int:
        prepare_id_for_query(_filter, is_mongo=True)
        update_fields = {'$set': cls._merge(_data, kwargs)}

        result = await cls.collection().update_many(_filter, update_fields)
        return result.modified_count
