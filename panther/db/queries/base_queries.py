import operator
from abc import abstractmethod
from functools import reduce
from sys import version_info
from typing import Iterator

from pydantic_core._pydantic_core import ValidationError

from panther.db.cursor import Cursor
from panther.db.utils import prepare_id_for_query
from panther.exceptions import DatabaseError

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseQuery')


class BaseQuery:
    @classmethod
    def _merge(cls, *args, is_mongo: bool = False) -> dict:
        prepare_id_for_query(*args, is_mongo=is_mongo)
        return reduce(operator.ior, filter(None, args), {})

    @classmethod
    def _clean_error_message(cls, validation_error: ValidationError, is_updating: bool = False) -> str:
        error = ', '.join(
            '{field}="{error}"'.format(
                field='.'.join(str(loc) for loc in e['loc']),
                error=e['msg']
            )
            for e in validation_error.errors()
            if not is_updating or e['type'] != 'missing'
        )
        return f'{cls.__name__}({error})' if error else ''

    @classmethod
    def _validate_data(cls, *, data: dict, is_updating: bool = False):
        """Validate document before inserting to collection"""
        try:
            cls(**data)
        except ValidationError as validation_error:
            if error := cls._clean_error_message(validation_error=validation_error, is_updating=is_updating):
                raise DatabaseError(error)

    @classmethod
    def _create_model_instance(cls, document: dict):
        """Prevent getting errors from document insertion"""
        try:
            return cls(**document)
        except ValidationError as validation_error:
            if error := cls._clean_error_message(validation_error=validation_error):
                raise DatabaseError(error)

    @classmethod
    @abstractmethod
    async def find_one(cls, *args, **kwargs) -> Self | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def find(cls, *args, **kwargs) -> list[Self] | Cursor:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def first(cls, *args, **kwargs) -> Self | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def last(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def aggregate(cls, *args, **kwargs) -> Iterator[dict]:
        raise NotImplementedError

    # # # # # Count # # # # #
    @classmethod
    @abstractmethod
    async def count(cls, *args, **kwargs) -> int:
        raise NotImplementedError

    # # # # # Insert # # # # #
    @classmethod
    @abstractmethod
    async def insert_one(cls, *args, **kwargs) -> Self:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def insert_many(cls, *args, **kwargs) -> list[Self]:
        raise NotImplementedError

    # # # # # Delete # # # # #
    @abstractmethod
    async def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def delete_one(cls, *args, **kwargs) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def delete_many(cls, *args, **kwargs) -> int:
        raise NotImplementedError

    # # # # # Update # # # # #
    @abstractmethod
    async def update(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def update_one(cls, *args, **kwargs) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def update_many(cls, *args, **kwargs) -> int:
        raise NotImplementedError
