from typing import Self

from panther.db.queries.mongodb_queries import BaseMongoDBQuery
from panther.db.queries.pantherdb_queries import BasePantherDBQuery
from panther.configs import config

if config['db_engine'] == 'pantherdb':
    BaseQuery = BasePantherDBQuery
else:
    BaseQuery = BaseMongoDBQuery

__all__ = (
    'Query',
)


class Query(BaseQuery):

    # # # # # Find # # # # #
    @classmethod
    def find_one(cls, _data: dict = None, /, **kwargs) -> Self | None:
        """
        example:
            >>> from example.app.models import User
            >>> User.find(id=1)
        """
        return super().find_one(_data, **kwargs)

    @classmethod
    def find(cls, _data: dict = None, /, **kwargs) -> list[Self]:
        """
        example:
            >>> from example.app.models import User
            >>> User.find(name='Ali')
        """
        return super().find(_data, **kwargs)

    # # # # # Insert # # # # #
    @classmethod
    def insert_one(cls, _data: dict = None, /, **kwargs) -> Self:
        """
        example:
            >>> from example.app.models import User
            >>> User.insert_one(name='Ali', age=24, ...)
        """
        return super().insert_one(_data, **kwargs)

    @classmethod
    def insert_many(cls, _data: dict = None, **kwargs):
        return super().insert_many(_data, **kwargs)

    # # # # # Delete # # # # #
    def delete(self) -> None:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.delete()
        """
        return super().delete()

    @classmethod
    def delete_one(cls, **kwargs) -> bool:
        """
        example:
            >>> from example.app.models import User
            >>> User.delete_one(id=1)
        """
        return super().delete_one(**kwargs)

    @classmethod
    def delete_many(cls, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.delete_many(last_name='Rn')
        """
        return super().delete_many(**kwargs)

    # # # # # Update # # # # #
    def update(self, **kwargs) -> None:
        """
        example:
            >>> from example.app.models import User
            >>> user = User.find_one(name='Ali')
            >>> user.update(name='Saba')
        """
        return super().update(**kwargs)

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> bool:
        """
        example:
            >>> from example.app.models import User
            >>> User.update_one({'id': 1}, name='Ali')
            >>> User.update_one({'id': 2}, {'name': 'Ali', 'age': 25})
        """
        return super().update_one(_filter, _data, **kwargs)

    @classmethod
    def update_many(cls, _filter, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.update_many({'name': 'Mohsen'}, name='Ali')
        """
        return super().update_many(_filter, **kwargs)

    # # # # # Other # # # # #
    @classmethod
    def first(cls, _data: dict = None, /, **kwargs) -> Self | None:
        """
        It works same as find_one()
        example:
            >>> from example.app.models import User
            >>> User.first(name='Ali')
        """
        return super().first(_data, **kwargs)

    @classmethod
    def last(cls, _data: dict = None, /, **kwargs) -> Self | None:
        """
        example:
            >>> from example.app.models import User
            >>> User.last(name='Ali')
        """
        return super().last(_data, **kwargs)

    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> User.count(name='Ali')
        """
        return super().count(_data, **kwargs)
