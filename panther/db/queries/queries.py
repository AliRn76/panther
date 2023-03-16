from typing import Self

from pydantic import ValidationError

from panther.configs import config
from panther.db.utils import log_query
from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.exceptions import DBException

if config['db_engine'] == 'pantherdb':
    BaseQuery = BasePantherDBQuery
else:
    BaseQuery = BaseMongoDBQuery

__all__ = (
    'Query',
)


class Query(BaseQuery):

    @classmethod
    def validate_data(cls, data: dict, is_updating: bool = False) -> Self | None:
        """
        *. Validate the input of user with its class
        *. If is_updating is True & exception happens but the message was empty
        """
        try:
            cls(**data)
        except ValidationError as validation_error:
            error = ', '.join(
                '{field}="{error}"'.format(field=e['loc'][0], error=e['msg'])
                for e in validation_error.errors() if not is_updating or e['type'] != 'value_error.missing')
            if error:
                message = f'{cls.__name__}({error})'
                raise DBException(message)

    # # # # # Find # # # # #
    @classmethod
    @log_query
    def find_one(cls, _data: dict = None, /, **kwargs) -> Self | None:
        """
        example:
            >>> from example.app.models import User
            >>> User.find(id=1)
        """
        return super().find_one(_data, **kwargs)

    @classmethod
    @log_query
    def find(cls, _data: dict = None, /, **kwargs) -> list[Self]:
        """
        example:
            >>> from example.app.models import User
            >>> User.find(name='Ali')
        """
        return super().find(_data, **kwargs)

    # # # # # Insert # # # # #
    @classmethod
    @log_query
    def insert_one(cls, _data: dict = None, /, **kwargs) -> Self:
        """
        example:
            >>> from example.app.models import User
            >>> User.insert_one(name='Ali', age=24, ...)
        """
        cls.validate_data(kwargs)
        return super().insert_one(_data, **kwargs)

    @classmethod
    @log_query
    def insert_many(cls, _data: dict = None, **kwargs):
        return super().insert_many(_data, **kwargs)

    # # # # # Delete # # # # #
    @log_query
    def delete(self) -> None:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.delete()
        """
        return super().delete()

    @classmethod
    @log_query
    def delete_one(cls, **kwargs) -> bool:
        """
        example:
            >>> from example.app.models import User
            >>> User.delete_one(id=1)
        """
        return super().delete_one(**kwargs)

    @classmethod
    @log_query
    def delete_many(cls, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.delete_many(last_name='Rn')
        """
        return super().delete_many(**kwargs)

    # # # # # Update # # # # #
    @log_query
    def update(self, **kwargs) -> None:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.update(name='Saba')
        """
        self.validate_data(kwargs, is_updating=True)
        return super().update(**kwargs)

    @classmethod
    @log_query
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> bool:
        """
        example:
            >>> from example.app.models import User
            >>> User.update_one({'id': 1}, name='Ali')
            >>> User.update_one({'id': 2}, {'name': 'Ali', 'age': 25})
        """
        return super().update_one(_filter, _data, **kwargs)

    @classmethod
    @log_query
    def update_many(cls, _filter, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.update_many({'name': 'Mohsen'}, name='Ali')
        """
        return super().update_many(_filter, **kwargs)

    # # # # # Other # # # # #
    @classmethod
    @log_query
    def last(cls, _data: dict = None, /, **kwargs) -> Self | None:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.last(name='Ali')
        """
        return super().last(_data, **kwargs)

    @classmethod
    @log_query
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.count(name='Ali')
        """
        return super().count(_data, **kwargs)

    @classmethod
    @log_query
    def find_or_insert(cls, **kwargs) -> tuple[bool, any]:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.find_or_insert(name='Ali')
        """
        if obj := cls.find_one(**kwargs):
            return False, obj
        else:
            return True, cls.insert_one(**kwargs)
