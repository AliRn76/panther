from __future__ import annotations

from sys import version_info
from typing import Iterable, Sequence

from panther.db.connections import db
from panther.db.cursor import Cursor
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import prepare_id_for_query

try:
    from bson.codec_options import CodecOptions
except ImportError:
    # This 'CodecOptions' is not going to be used,
    #   If user really wants to use it,
    #   we are going to force him to install it in `panther.db.connections.MongoDBConnection.init`
    CodecOptions = type('CodecOptions', (), {})

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseMongoDBQuery')


class BaseMongoDBQuery(BaseQuery):
    @classmethod
    def _merge(cls, *args, is_mongo: bool = True) -> dict:
        return super()._merge(*args, is_mongo=is_mongo)

    # TODO: https://jira.mongodb.org/browse/PYTHON-4192
    # @classmethod
    # def collection(cls):
    #     return db.session.get_collection(name=cls.__name__, codec_options=CodecOptions(document_class=cls))

    # # # # # Find # # # # #
    @classmethod
    async def find_one(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        if document := await db.session[cls.__name__].find_one(cls._merge(_filter, kwargs)):
            return cls._create_model_instance(document=document)
        return None

    @classmethod
    async def find(cls, _filter: dict | None = None, /, **kwargs) -> Cursor:
        return Cursor(cls=cls, collection=db.session[cls.__name__].delegate, filter=cls._merge(_filter, kwargs))

    @classmethod
    async def first(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        cursor = await cls.find(_filter, **kwargs)
        for result in cursor.sort('_id', 1).limit(-1):
            return result
        return None

    @classmethod
    async def last(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        cursor = await cls.find(_filter, **kwargs)
        for result in cursor.sort('_id', -1).limit(-1):
            return result
        return None

    @classmethod
    async def aggregate(cls, pipeline: Sequence[dict]) -> Iterable[dict]:
        return await db.session[cls.__name__].aggregate(pipeline).to_list(None)

    # # # # # Count # # # # #
    @classmethod
    async def count(cls, _filter: dict | None = None, /, **kwargs) -> int:
        return await db.session[cls.__name__].count_documents(cls._merge(_filter, kwargs))

    # # # # # Insert # # # # #
    @classmethod
    async def insert_one(cls, _document: dict | None = None, /, **kwargs) -> Self:
        document = cls._merge(_document, kwargs)
        cls._validate_data(data=document)

        await db.session[cls.__name__].insert_one(document)
        return cls._create_model_instance(document=document)

    @classmethod
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        for document in documents:
            prepare_id_for_query(document, is_mongo=True)
            cls._validate_data(data=document)

        await db.session[cls.__name__].insert_many(documents)
        return [cls._create_model_instance(document=document) for document in documents]

    # # # # # Delete # # # # #
    async def delete(self) -> None:
        await db.session[self.__class__.__name__].delete_one({'_id': self._id})

    @classmethod
    async def delete_one(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        result = await db.session[cls.__name__].delete_one(cls._merge(_filter, kwargs))
        return bool(result.deleted_count)

    @classmethod
    async def delete_many(cls, _filter: dict | None = None, /, **kwargs) -> int:
        result = await db.session[cls.__name__].delete_many(cls._merge(_filter, kwargs))
        return result.deleted_count

    # # # # # Update # # # # #
    async def update(self, _update: dict | None = None, /, **kwargs) -> None:
        merged_update_query = self._merge(_update, kwargs)
        merged_update_query.pop('_id', None)

        self._validate_data(data=merged_update_query, is_updating=True)

        update_query = {}
        for field, value in merged_update_query.items():
            if field.startswith('$'):
                update_query[field] = value
            else:
                update_query['$set'] = update_query.get('$set', {})
                update_query['$set'][field] = value
                if isinstance(value, dict):
                    value = type(getattr(self, field))(**value)
                setattr(self, field, value)

        await db.session[self.__class__.__name__].update_one({'_id': self._id}, update_query)

    @classmethod
    async def update_one(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> bool:
        prepare_id_for_query(_filter, is_mongo=True)
        merged_update_query = cls._merge(_update, kwargs)

        update_query = {}
        for field, value in merged_update_query.items():
            if field.startswith('$'):
                update_query[field] = value
            else:
                update_query['$set'] = update_query.get('$set', {})
                update_query['$set'][field] = value

        result = await db.session[cls.__name__].update_one(_filter, update_query)
        return bool(result.matched_count)

    @classmethod
    async def update_many(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> int:
        prepare_id_for_query(_filter, is_mongo=True)
        update_fields = {'$set': cls._merge(_update, kwargs)}

        result = await db.session[cls.__name__].update_many(_filter, update_fields)
        return result.modified_count
