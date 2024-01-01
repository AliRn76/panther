import sys

from pydantic import ValidationError

from panther import status
from panther.configs import config
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.db.utils import log_query, check_connection
from panther.exceptions import APIException, DBException

BaseQuery = BasePantherDBQuery if config['db_engine'] == 'pantherdb' else BaseMongoDBQuery

__all__ = ('Query',)


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='Query')


class Query(BaseQuery):
    @classmethod
    def validate_data(cls, *, data: dict, is_updating: bool = False):
        """
        *. Validate the input of user with its class
        *. If is_updating is True & exception happens but the message was empty
        """
        try:
            cls(**data)
        except ValidationError as validation_error:
            error = {
                '.'.join(loc for loc in e['loc']): e['msg']
                for e in validation_error.errors()
                if not is_updating or e['type'] != 'missing'
            }
            if error:
                raise APIException(detail=error, status_code=status.HTTP_400_BAD_REQUEST)

    @classmethod
    def create_model_instance(cls, document: dict):
        try:
            return cls(**document)
        except ValidationError as validation_error:
            error = ', '.join(
                '{field}="{error}"'.format(field='.'.join(loc for loc in e['loc']), error=e['msg'])
                for e in validation_error.errors()
            )
            if error:
                message = f'{cls.__name__}({error})'
                raise DBException(message)

    # # # # # Find # # # # #
    @classmethod
    @check_connection
    @log_query
    def find_one(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.find_one(id=1)
        """
        return super().find_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def find(cls, _data: dict | None = None, /, **kwargs) -> list[Self]:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.find(name='Ali')
        """
        return super().find(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def first(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.first(name='Ali')
        * Alias of find_one()
        """
        return super().first(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def last(cls, _data: dict | None = None, /, **kwargs) -> Self | None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.last(name='Ali')
        """
        return super().last(_data, **kwargs)

    # # # # # Count # # # # #
    @classmethod
    @check_connection
    @log_query
    def count(cls, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.count(name='Ali')
        """
        return super().count(_data, **kwargs)

    # # # # # Insert # # # # #
    @classmethod
    @check_connection
    @log_query
    def insert_one(cls, _data: dict | None = None, /, **kwargs) -> Self:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.insert_one(name='Ali', age=24, ...)
        """
        cls.validate_data(data=kwargs)
        return super().insert_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def insert_many(cls, _data: dict | None = None, /, **kwargs):
        msg = 'insert_many() is not supported yet.'
        raise DBException(msg)

    # # # # # Delete # # # # #
    @check_connection
    @log_query
    def delete(self) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.delete()
        """
        return super().delete()

    @classmethod
    @check_connection
    @log_query
    def delete_one(cls, _data: dict | None = None, /, **kwargs) -> bool:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.delete_one(id=1)
        """
        return super().delete_one(_data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def delete_many(cls, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.delete_many(last_name='Rn')
        """
        return super().delete_many(_data, **kwargs)

    # # # # # Update # # # # #
    @check_connection
    @log_query
    def update(self, **kwargs) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.update(name='Saba')
        """
        self.validate_data(data=kwargs, is_updating=True)
        return super().update(**kwargs)

    @classmethod
    @check_connection
    @log_query
    def update_one(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> bool:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.update_one({'id': 1}, name='Ali')
            >>> User.update_one({'id': 2}, {'name': 'Ali', 'age': 25})
        """
        return super().update_one(_filter, _data, **kwargs)

    @classmethod
    @check_connection
    @log_query
    def update_many(cls, _filter: dict, _data: dict | None = None, /, **kwargs) -> int:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.update_many({'name': 'Mohsen'}, name='Ali')
            >>> User.update_many({'name': 'Mohsen'}, {'name': 'Ali'})
        """
        return super().update_many(_filter, _data, **kwargs)

    # # # # # Other # # # # #
    @classmethod
    def all(cls) -> list[Self]:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> User.all()
        * Alias of find() without args
        """
        return cls.find()

    @classmethod
    def find_or_insert(cls, **kwargs) -> tuple[bool, any]:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.find_or_insert(name='Ali')
        """
        if obj := cls.find_one(**kwargs):
            return False, obj
        return True, cls.insert_one(**kwargs)

    @classmethod
    def find_one_or_raise(cls, **kwargs) -> Self:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.find_one_or_raise(name='Ali')
        """
        if obj := cls.find_one(**kwargs):
            return obj

        raise APIException(
            detail=f'{cls.__name__} Does Not Exists',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @check_connection
    @log_query
    def save(self) -> None:
        """
        Example:
        -------
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.name = 'Saba'
            >>> user.save()
        """
        msg = 'save() is not supported yet.'
        raise DBException(msg) from None
