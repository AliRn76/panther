from __future__ import annotations

import typing
from sys import version_info

from panther.db.connections import db
from panther.db.cursor import Cursor
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import prepare_id_for_query

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

try:
    from bson.codec_options import CodecOptions
    from pymongo.results import InsertManyResult, InsertOneResult
except ImportError:
    # MongoDB-related libraries are not required by default.
    # If the user intends to use MongoDB, they must install the required dependencies explicitly.
    # This will be enforced in `panther.db.connections.MongoDBConnection.init`.
    CodecOptions = type('CodecOptions', (), {})
    InsertOneResult = type('InsertOneResult', (), {})
    InsertManyResult = type('InsertManyResult', (), {})

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
            return await cls._create_model_instance(document=document)
        return None

    @classmethod
    async def find(cls, _filter: dict | None = None, /, **kwargs) -> Cursor:
        return Cursor(cls=cls, collection=db.session[cls.__name__].delegate, filter=cls._merge(_filter, kwargs))

    @classmethod
    async def first(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        cursor = await cls.find(_filter, **kwargs)
        async for result in cursor.sort('_id', 1).limit(-1):
            return result
        return None

    @classmethod
    async def last(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        cursor = await cls.find(_filter, **kwargs)
        async for result in cursor.sort('_id', -1).limit(-1):
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
    async def insert_one(cls, document: dict) -> Self:
        insert_one_result: InsertOneResult = await db.session[cls.__name__].insert_one(document)
        return insert_one_result.inserted_id

    @classmethod
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        final_documents = []
        results = []
        for document in documents:
            prepare_id_for_query(document, is_mongo=True)
            final_document = await cls._process_document(document)
            final_documents.append(final_document)
            results.append(await cls._create_model_instance(document=final_document))
        insert_many_result: InsertManyResult = await db.session[cls.__name__].insert_many(final_documents)
        for obj, inserted_id in zip(results, insert_many_result.inserted_ids):
            obj.id = inserted_id
        return results

    # # # # # Delete # # # # #
    @classmethod
    async def delete_one(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        result = await db.session[cls.__name__].delete_one(cls._merge(_filter, kwargs))
        return bool(result.deleted_count)

    @classmethod
    async def delete_many(cls, _filter: dict | None = None, /, **kwargs) -> int:
        result = await db.session[cls.__name__].delete_many(cls._merge(_filter, kwargs))
        return result.deleted_count

    # # # # # Update # # # # #
    @classmethod
    async def update_one(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> bool:
        prepare_id_for_query(_filter, is_mongo=True)

        # Step 1: Merge document parameters
        # Combine the _update dict with keyword arguments into a single document
        document = cls._merge(_update, kwargs)

        # Step 2: Process and validate document
        # - Validate data types and structure
        # - Convert Model instances to their IDs for database storage
        # - Handle File objects by saving to disk and storing file paths
        # - Process nested objects and relationships
        final_document = await cls._process_document(document)

        # Step 3: Create model instance (Validating)
        # - Retrieve Model instances from database using IDs
        # - Open File objects from their stored paths
        # - Build the complete model instance with all relationships
        await cls._create_model_instance(document=final_document, is_updating=True)

        # Step 4: Create the query
        update_query = {}
        for field, value in final_document.items():
            if field.startswith('$'):
                update_query[field] = value
            else:
                if not '$set' in update_query:
                    update_query['$set'] = {}
                update_query['$set'][field] = value

        result = await db.session[cls.__name__].update_one(_filter, update_query)
        return bool(result.matched_count)

    @classmethod
    async def update_many(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> int:
        prepare_id_for_query(_filter, is_mongo=True)

        # Step 1: Merge document parameters
        # Combine the _update dict with keyword arguments into a single document
        document = cls._merge(_update, kwargs)

        # Step 2: Process and validate document
        # - Validate data types and structure
        # - Convert Model instances to their IDs for database storage
        # - Handle File objects by saving to disk and storing file paths
        # - Process nested objects and relationships
        final_document = await cls._process_document(document)

        # Step 3: Create model instance (Validating)
        # - Retrieve Model instances from database using IDs
        # - Open File objects from their stored paths
        # - Build the complete model instance with all relationships
        await cls._create_model_instance(document=final_document, is_updating=True)

        # Step 4: Create the query
        update_query = {}
        for field, value in final_document.items():
            if field.startswith('$'):
                update_query[field] = value
            else:
                if not '$set' in update_query:
                    update_query['$set'] = {}
                update_query['$set'][field] = value

        result = await db.session[cls.__name__].update_many(_filter, update_query)
        return result.modified_count
