from __future__ import annotations

import types
import typing
from sys import version_info
from typing import get_args, get_origin, Iterable, Sequence, Any, Union

from pydantic import BaseModel, ValidationError

from panther.db.connections import db
from panther.db.cursor import Cursor
from panther.db.models import Model
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import prepare_id_for_query
from panther.exceptions import DatabaseError

try:
    from bson.codec_options import CodecOptions
    from pymongo.results import InsertOneResult, InsertManyResult
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


def get_annotation_type(annotation: Any) -> type | None:
    """
    Extracts the underlying, non-optional type from a type annotation.
    Handles basic types, Pydantic BaseModels, lists, and unions (optionals).
    Returns None if no single underlying type can be determined (e.g., for list[NoneType]).
    Raises DatabaseError for unsupported annotations.
    """
    origin = get_origin(annotation)

    # Handle list[T] and Union[T, None] (T | None or typing.Union[T, None])
    if origin is list or origin is types.UnionType or origin is Union:
        # Extracts the first non-None type from a tuple of type arguments.
        for arg in get_args(annotation):
            if arg is not type(None):
                return arg
        return None

    # Handle basic types (str, int, bool, dict) and Pydantic BaseModel subclasses
    if isinstance(annotation, type) and (
            annotation in (str, int, bool, dict) or issubclass(annotation, BaseModel)
    ):
        return annotation

    raise DatabaseError(f'Panther does not support {annotation} as a field type for unwrapping.')


class BaseMongoDBQuery(BaseQuery):
    @classmethod
    def _merge(cls, *args, is_mongo: bool = True) -> dict:
        return super()._merge(*args, is_mongo=is_mongo)

    # TODO: https://jira.mongodb.org/browse/PYTHON-4192
    # @classmethod
    # def collection(cls):
    #     return db.session.get_collection(name=cls.__name__, codec_options=CodecOptions(document_class=cls))

    @classmethod
    async def _create_list(cls, field_type: type, value: Any) -> Any:
        # `field_type` is the expected type of items in the list (e.g., int, Model, list[str])
        # `value` is a single item from the input list that needs processing.

        # Handles list[list[int]], list[dict[str,int]] etc.
        if isinstance(field_type, (types.GenericAlias, typing._GenericAlias)):
            element_type = get_annotation_type(field_type)  # Unwrap further (e.g. list[str] -> str)
            if element_type is None:
                raise DatabaseError(f"Cannot determine element type for generic list item: {field_type}")
            if not isinstance(value, list):  # Or check if iterable, matching the structure
                raise DatabaseError(f"Expected a list for nested generic type {field_type}, got {type(value)}")
            return [await cls._create_list(field_type=element_type, value=item) for item in value]

        # Make sure Model condition is before BaseModel.
        if isinstance(field_type, type) and issubclass(field_type, Model):
            # `value` is assumed to be an ID for the Model instance.
            return await field_type.first(id=value)

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            if not isinstance(value, dict):
                raise DatabaseError(f"Expected a dictionary for BaseModel {field_type.__name__}, got {type(value)}")

            return {
                field_name: await cls._create_field(model=field_type, field_name=field_name, value=value[field_name])
                for field_name in value
            }

        # Base case: value is a primitive type (str, int, etc.)
        return value

    @classmethod
    async def _create_field(cls, model: type, field_name: str, value: Any) -> Any:
        # Handle primary key field directly
        if field_name == '_id':
            return value

        if field_name not in model.model_fields:
            # Field from input data is not defined in the model.
            # Pydantic's `extra` config on the model will handle this upon instantiation.
            return value

        field_annotation = model.model_fields[field_name].annotation
        unwrapped_type = get_annotation_type(field_annotation)

        if unwrapped_type is None:
            raise DatabaseError(
                f"Could not determine a valid underlying type for field '{field_name}' "
                f"with annotation {field_annotation} in model {model.__name__}."
            )

        if get_origin(field_annotation) is list:
            # Or check for general iterables if applicable
            if not isinstance(value, list):
                raise DatabaseError(
                    f"Field '{field_name}' expects a list, got {type(value)} for model {model.__name__}")
            return [await cls._create_list(field_type=unwrapped_type, value=item) for item in value]

        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, Model):
            if obj := await unwrapped_type.first(id=value):
                return obj.model_dump(by_alias=True)
            return None

        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, BaseModel):
            if not isinstance(value, dict):
                raise DatabaseError(
                    f"Field '{field_name}' expects a dictionary for BaseModel {unwrapped_type.__name__}, "
                    f"got {type(value)} in model {model.__name__}"
                )
            return {
                nested_field_name: await cls._create_field(
                    model=unwrapped_type,
                    field_name=nested_field_name,
                    value=value[nested_field_name],
                )
                for nested_field_name in unwrapped_type.model_fields if nested_field_name in value
            }

        return value

    @classmethod
    async def _create_model_instance(cls, document: dict) -> Self:
        """Prepares document and creates an instance of the model."""
        processed_document = {
            field_name: await cls._create_field(model=cls, field_name=field_name, value=field_value)
            for field_name, field_value in document.items()
        }
        try:
            return cls(**processed_document)
        except ValidationError as validation_error:
            error = cls._clean_error_message(validation_error=validation_error)
            raise DatabaseError(error) from validation_error

    @classmethod
    def clean_value(cls, field: str | None, value: Any) -> dict[str, Any] | list[Any]:
        match value:
            case None:
                return None
            case Model() as model:
                if model.id is None:
                    raise DatabaseError(f'Model instance{" in " + field if field else ""} has no ID.')
                # We save full object because user didn't specify the type.
                return model._id
            case BaseModel() as model:
                return {
                    field_name: cls.clean_value(field=field_name, value=getattr(model, field_name))
                    for field_name in model.model_fields
                }
            case dict() as d:
                return {k: cls.clean_value(field=k, value=v) for k, v in d.items()}
            case list() as l:
                return [cls.clean_value(field=None, value=item) for item in l]

        return value

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
    async def insert_one(cls, _document: dict | None = None, /, **kwargs) -> Self:
        document = cls._merge(_document, kwargs)
        cls._validate_data(data=document)
        final_document = {
            field: cls.clean_value(field=field, value=value)
            for field, value in document.items()
        }
        result = await cls._create_model_instance(document=final_document)
        insert_one_result: InsertOneResult = await db.session[cls.__name__].insert_one(final_document)
        result.id = insert_one_result.inserted_id
        return result

    @classmethod
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        final_documents = []
        results = []
        for document in documents:
            prepare_id_for_query(document, is_mongo=True)
            cls._validate_data(data=document)
            cleaned_document = {
                field: cls.clean_value(field=field, value=value)
                for field, value in document.items()
            }
            final_documents.append(cleaned_document)
            results.append(await cls._create_model_instance(document=cleaned_document))
        insert_many_result: InsertManyResult = await db.session[cls.__name__].insert_many(final_documents)
        for obj, _id in zip(results, insert_many_result.inserted_ids):
            obj.id = _id
        return results

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
