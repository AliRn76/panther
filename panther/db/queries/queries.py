import sys

from pydantic import ValidationError

from panther.configs import QueryObservable
from panther.db.cursor import Cursor
from panther.db.utils import log_query, check_connection
from panther.exceptions import DatabaseError, NotFoundAPIError

__all__ = ('Query',)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='Query')


class Query:
    def __init_subclass__(cls, **kwargs):
        QueryObservable.observe(cls)

    @classmethod
    def _reload_bases(cls, parent):
        if cls.__bases__.count(Query):
            cls.__bases__ = (*cls.__bases__[: cls.__bases__.index(Query) + 1], parent)
        else:
            for kls in cls.__bases__:
                if kls.__bases__.count(Query):
                    kls.__bases__ = (*kls.__bases__[:kls.__bases__.index(Query) + 1], parent)

    @classmethod
    def _clean_error_message(cls, validation_error: ValidationError, is_updating: bool = False) -> str:
        error = ', '.join(
            '{field}="{error}"'.format(
                field='.'.join(loc for loc in e['loc']),
                error=e['msg']
            )
            for e in validation_error.errors()
            if not is_updating or e['type'] != 'missing'
        )
        return f'{cls.__name__}({error})' if error else ''

    @classmethod
    def _validate_data(cls, *, data: dict, is_updating: bool = False):
        """Validate data before inserting to db"""
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

    # # # # # Find # # # # #
    @classmethod
    @check_connection
    @log_query
    async def find_one(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.find_one(id=1)
        """
        return await super().find_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def find(cls, _data: dict | None = None, /, **kwargs) -> list[Self] | Cursor:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.find(name='Ali')
        """
        return await super().find(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def first(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.first(name='Ali')
        * Alias of find_one()
        """
        return await super().first(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def last(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.last(name='Ali')
        """
        return await super().last(_data, **kwargs)

    # # # # # Count # # # # #
    @classmethod
    @check_connection
    @log_query
    async def count(cls, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.count(name='Ali')
        """
        return await super().count(_data, **kwargs)

    # # # # # Insert # # # # #
    @classmethod
    @check_connection
    @log_query
    async def insert_one(cls, _data: dict | None = None, /, **kwargs) -> Self:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.insert_one(name='Ali', age=24, ...)
        """
        cls._validate_data(data=(_data or {}) | kwargs)
        return await super().insert_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def insert_many(cls, _data: dict | None = None, /, **kwargs):
        msg = 'insert_many() is not supported yet.'
        raise DatabaseError(msg)

    # # # # # Delete # # # # #
    @check_connection
    @log_query
    async def delete(self) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.find_one(name='Ali')
            >>> await user.delete()
        """
        await super().delete()

    @classmethod
    @check_connection
    @log_query
    async def delete_one(cls, _data: dict | None = None, /, **kwargs) -> bool:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.delete_one(id=1)
        """
        return await super().delete_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def delete_many(cls, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.delete_many(last_name='Rn')
        """
        return await super().delete_many(_data, **kwargs)

    # # # # # Update # # # # #
    @check_connection
    @log_query
    async def update(self, **kwargs) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.find_one(name='Ali')
            >>> await user.update(name='Saba')
        """
        self._validate_data(data=kwargs, is_updating=True)
        await super().update(**kwargs)

    @classmethod
    @check_connection
    @log_query
    async def update_one(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> bool:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.update_one({'id': 1}, name='Ali')
            >>> await User.update_one({'id': 2}, {'name': 'Ali', 'age': 25})
        """
        return await super().update_one(_filter, _data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def update_many(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.update_many({'name': 'Mohsen'}, name='Ali')
            >>> await User.update_many({'name': 'Mohsen'}, {'name': 'Ali'})
        """
        return await super().update_many(_filter, _data, **kwargs)

    # # # # # Other # # # # #
    @classmethod
    async def all(cls) -> list[Self] | Cursor:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> await User.all()
        * Alias of find() without args
        """
        return await cls.find()

    @classmethod
    async def find_or_insert(cls, **kwargs) -> tuple[bool, any]:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.find_or_insert(name='Ali')
        """
        if obj := await cls.find_one(**kwargs):
            return False, obj
        return True, await cls.insert_one(**kwargs)

    @classmethod
    async def find_one_or_raise(cls, **kwargs) -> Self:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.find_one_or_raise(name='Ali')
        """
        if obj := await cls.find_one(**kwargs):
            return obj

        raise NotFoundAPIError(detail=f'{cls.__name__} Does Not Exists')

    @check_connection
    @log_query
    async def save(self) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = await User.find_one(name='Ali')
            >>> user.name = 'Saba'
            >>> await user.save()
        """
        msg = 'save() is not supported yet.'
        raise DatabaseError(msg) from None
