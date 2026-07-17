from __future__ import annotations

import operator
import sys
import types
import typing
from datetime import datetime
from functools import reduce
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

from panther._utils import detect_mime_type
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import prepare_id_for_query
from panther.exceptions import DatabaseError
from panther.file_handler import File

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseDocumentQuery')


class BaseDocumentQuery(BaseQuery):
    """Document-model behavior shared by PantherDB and MongoDB query engines."""

    @classmethod
    def _merge(cls, *args, is_mongo: bool = False) -> dict:
        prepare_id_for_query(*args, is_mongo=is_mongo)
        return reduce(operator.ior, filter(None, args), {})

    @classmethod
    def _clean_error_message(cls, validation_error: ValidationError, is_updating: bool = False) -> str:
        error = ', '.join(
            '{field}="{error}"'.format(field='.'.join(str(loc) for loc in e['loc']), error=e['msg'])
            for e in validation_error.errors()
            if not is_updating or e['type'] != 'missing'
        )
        return f'{cls.__name__}({error})' if error else ''

    @classmethod
    def _validate_data(cls, *, data: dict, is_updating: bool = False):
        """Validate a document before inserting it into a collection."""
        try:
            cls(**data)
        except ValidationError as validation_error:
            if error := cls._clean_error_message(validation_error=validation_error, is_updating=is_updating):
                raise DatabaseError(error)

    @classmethod
    def _get_annotation_type(cls, annotation: Any) -> type | None:
        origin = get_origin(annotation)
        if origin is list or origin is types.UnionType or origin is Union:
            for arg in get_args(annotation):
                if arg is not type(None):
                    return arg
            return None

        try:
            if isinstance(annotation, type) and (
                annotation in (str, int, bool, dict, float, datetime) or issubclass(annotation, (BaseModel, File))
            ):
                return annotation
        except TypeError:
            pass
        raise DatabaseError(f'Panther does not support {annotation} as a field type for unwrapping.')

    @classmethod
    async def _create_list(cls, field_type: type, value: Any) -> Any:
        from panther.db import DocumentModel

        if isinstance(field_type, (types.GenericAlias, typing._GenericAlias)):
            element_type = cls._get_annotation_type(field_type)
            if element_type is None:
                raise DatabaseError(f'Cannot determine element type for generic list item: {field_type}')
            if not isinstance(value, list):
                raise DatabaseError(f'Expected a list for nested generic type {field_type}, got {type(value)}')
            return [await cls._create_list(field_type=element_type, value=item) for item in value]

        if isinstance(field_type, type) and issubclass(field_type, DocumentModel):
            return await field_type.first(id=value)

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            if not isinstance(value, dict):
                raise DatabaseError(f'Expected a dictionary for BaseModel {field_type.__name__}, got {type(value)}')
            return {
                field_name: await cls._create_field(model=field_type, field_name=field_name, value=value[field_name])
                for field_name in value
            }
        return value

    @classmethod
    async def _create_field(cls, model: type, field_name: str, value: Any) -> Any:
        from panther.db import DocumentModel

        if field_name == 'id' or field_name not in model.model_fields:
            return value

        field_annotation = model.model_fields[field_name].annotation
        unwrapped_type = cls._get_annotation_type(field_annotation)
        if unwrapped_type is None:
            raise DatabaseError(
                f"Could not determine a valid underlying type for field '{field_name}' "
                f'with annotation {field_annotation} in model {model.__name__}.',
            )

        if get_origin(field_annotation) is list:
            if not isinstance(value, list):
                raise DatabaseError(
                    f"Field '{field_name}' expects a list, got {type(value)} for model {model.__name__}",
                )
            return [await cls._create_list(field_type=unwrapped_type, value=item) for item in value]

        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, File):
            content_type = detect_mime_type(file_path=value)
            with open(value, 'rb') as f:
                return File(file_name=value, content_type=content_type, file=f.read()).model_dump()

        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, DocumentModel):
            if obj := await unwrapped_type.first(id=value):
                return obj.model_dump()
            return None

        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, BaseModel):
            if not isinstance(value, dict):
                raise DatabaseError(
                    f"Field '{field_name}' expects a dictionary for BaseModel {unwrapped_type.__name__}, "
                    f'got {type(value)} in model {model.__name__}',
                )
            return {
                nested_field_name: await cls._create_field(
                    model=unwrapped_type,
                    field_name=nested_field_name,
                    value=value[nested_field_name],
                )
                for nested_field_name in unwrapped_type.model_fields
                if nested_field_name in value
            }
        return value

    @classmethod
    async def _create_model_instance(cls, document: dict, is_updating: bool = False) -> Self:
        """Create a model instance from a database document."""
        if '_id' in document:
            document['id'] = document.pop('_id')

        processed_document = {
            field_name: await cls._create_field(model=cls, field_name=field_name, value=field_value)
            for field_name, field_value in document.items()
        }
        try:
            return cls(**processed_document)
        except ValidationError as validation_error:
            if error := cls._clean_error_message(validation_error=validation_error, is_updating=is_updating):
                raise DatabaseError(error) from validation_error

    @classmethod
    async def _clean_value(cls, value: Any) -> dict[str, Any] | list[Any]:
        from panther.db import DocumentModel

        match value:
            case None:
                return None
            case DocumentModel() as model:
                if model.id in [None, '']:
                    await model.save()
                return model._id
            case File() as file:
                return file.save()
            case BaseModel() as model:
                return {
                    field_name: await cls._clean_value(value=getattr(model, field_name))
                    for field_name in model.__class__.model_fields
                }
            case dict() as d:
                return {k: await cls._clean_value(value=v) for k, v in d.items()}
            case list() as l:
                return [await cls._clean_value(value=item) for item in l]
        return value

    @classmethod
    async def _extract_type(cls, field_name: str) -> Any:
        if field_name not in cls.model_fields:
            return None
        field_annotation = cls.model_fields[field_name].annotation
        unwrapped_type = cls._get_annotation_type(field_annotation)
        if (
            get_origin(field_annotation) is list
            and isinstance(unwrapped_type, type)
            and issubclass(unwrapped_type, BaseModel)
        ):
            return list[unwrapped_type]
        if isinstance(unwrapped_type, type) and issubclass(unwrapped_type, BaseModel):
            return unwrapped_type

    @classmethod
    async def _process_document(cls, document):
        processed_document = {}
        for field_name, field_value in document.items():
            if field_name in ['id', '_id']:
                continue
            field_type = await cls._extract_type(field_name)
            if field_type:
                if get_origin(field_type) is list:
                    cls_type = cls._get_annotation_type(field_type)
                    value = [cls_type(**v) if isinstance(v, dict) else v for v in field_value]
                elif isinstance(field_value, dict):
                    value = field_type(**field_value)
                else:
                    value = field_value
            else:
                value = field_value
            processed_document[field_name] = await cls._clean_value(value)
        return processed_document
