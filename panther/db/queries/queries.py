import sys
from typing import Sequence, Iterable

from pantherdb import Cursor as PantherDBCursor
from pydantic import BaseModel

from panther.configs import QueryObservable
from panther.db.cursor import Cursor
from panther.db.queries.base_queries import BaseQuery
from panther.db.utils import log_query, check_connection
from panther.exceptions import NotFoundAPIError

__all__ = ('Query',)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='Query')


class Query(BaseQuery):
    def __init_subclass__(cls, **kwargs):
        QueryObservable.observe(cls)

    @classmethod
    def _reload_bases(cls, parent):
        if not issubclass(parent, BaseQuery):
            msg = f'Invalid Query Class: `{parent.__name__}` should be subclass of `BaseQuery`'
            raise ValueError(msg)

        if cls.__bases__.count(Query):
            cls.__bases__ = (*cls.__bases__[: cls.__bases__.index(Query) + 1], parent)
        else:
            for kls in cls.__bases__:
                if kls.__bases__.count(Query):
                    kls.__bases__ = (*kls.__bases__[:kls.__bases__.index(Query) + 1], parent)

    # # # # # Find # # # # #
    @classmethod
    @check_connection
    @log_query
    async def find_one(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        """
        Get a single document from the database.

        Example:
        -------
            >>> from app.models import User

            >>> await User.find_one(id=1, name='Ali')
            or
            >>> await User.find_one({'id': 1, 'name': 'Ali'})
            or
            >>> await User.find_one({'id': 1}, name='Ali')
        """
        return await super().find_one(_filter, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def find(cls, _filter: dict | None = None, /, **kwargs) -> PantherDBCursor | Cursor:
        """
        Get documents from the database.

        Example:
        -------
            >>> from app.models import User

            >>> await User.find(age=18, name='Ali')
            or
            >>> await User.find({'age': 18, 'name': 'Ali'})
            or
            >>> await User.find({'age': 18}, name='Ali')
        """
        return await super().find(_filter, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def first(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        """
        Get the first document from the database.

        Example:
        -------
            >>> from app.models import User

            >>> await User.first(age=18, name='Ali')
            or
            >>> await User.first({'age': 18, 'name': 'Ali'})
            or
            >>> await User.first({'age': 18}, name='Ali')
        """
        return await super().first(_filter, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def last(cls, _filter: dict | None = None, /, **kwargs) -> Self | None:
        """
        Get the last document from the database.

        Example:
        -------
            >>> from app.models import User

            >>> await User.last(age=18, name='Ali')
            or
            >>> await User.last({'age': 18, 'name': 'Ali'})
            or
            >>> await User.last({'age': 18}, name='Ali')
        """
        return await super().last(_filter, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def aggregate(cls, pipeline: Sequence[dict]) -> Iterable[dict]:
        """
        Perform an aggregation using the aggregation framework on this collection.

        Example:
        -------
            >>> from app.models import User

            >>> pipeline = [
            >>>     {'$match': {...}},
            >>>     {'$unwind': ...},
            >>>     {'$group': {...}},
            >>>     {'$project': {...}},
            >>>     {'$sort': {...}}
            >>>     ...
            >>> ]

            >>> await User.aggregate(pipeline)
        """
        return await super().aggregate(pipeline)

    # # # # # Count # # # # #
    @classmethod
    @check_connection
    @log_query
    async def count(cls, _filter: dict | None = None, /, **kwargs) -> int:
        """
        Count the number of documents in this collection.

        Example:
        -------
            >>> from app.models import User

            >>> await User.count(age=18, name='Ali')
            or
            >>> await User.count({'age': 18, 'name': 'Ali'})
            or
            >>> await User.count({'age': 18}, name='Ali')
        """
        return await super().count(_filter, **kwargs)

    # # # # # Insert # # # # #
    @classmethod
    @check_connection
    @log_query
    async def insert_one(cls, _document: dict | None = None, /, **kwargs) -> Self:
        """
        Insert a single document.

        Example:
        -------
            >>> from app.models import User

            >>> await User.insert_one(age=18, name='Ali')
            or
            >>> await User.insert_one({'age': 18, 'name': 'Ali'})
            or
            >>> await User.insert_one({'age': 18}, name='Ali')
        """
        return await super().insert_one(_document, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def insert_many(cls, documents: Iterable[dict]) -> list[Self]:
        """
        Insert an iterable of documents.

        Example:
        -------
            >>> from app.models import User

            >>> users = [
            >>>     {'age': 18, 'name': 'Ali'},
            >>>     {'age': 17, 'name': 'Saba'},
            >>>     {'age': 16, 'name': 'Amin'}
            >>> ]
            >>> await User.insert_many(users)
        """
        return await super().insert_many(documents)

    # # # # # Delete # # # # #
    @check_connection
    @log_query
    async def delete(self) -> None:
        """
        Delete the document.

        Example:
        -------
            >>> from app.models import User

            >>> user = await User.find_one(name='Ali')

            >>> await user.delete()
        """
        await super().delete()

    @classmethod
    @check_connection
    @log_query
    async def delete_one(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        """
        Delete a single document matching the filter.

        Example:
        -------
            >>> from app.models import User

            >>> await User.delete_one(age=18, name='Ali')
            or
            >>> await User.delete_one({'age': 18, 'name': 'Ali'})
            or
            >>> await User.delete_one({'age': 18}, name='Ali')
        """
        return await super().delete_one(_filter, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def delete_many(cls, _filter: dict | None = None, /, **kwargs) -> int:
        """
        Delete one or more documents matching the filter.

        Example:
        -------
            >>> from app.models import User

            >>> await User.delete_many(age=18, name='Ali')
            or
            >>> await User.delete_many({'age': 18, 'name': 'Ali'})
            or
            >>> await User.delete_many({'age': 18}, name='Ali')
        """
        return await super().delete_many(_filter, **kwargs)

    # # # # # Update # # # # #
    @check_connection
    @log_query
    async def update(self, _update: dict | None = None, /, **kwargs) -> None:
        """
        Update the document.

        Example:
        -------
            >>> from app.models import User

            >>> user = await User.find_one(age=18, name='Ali')

            >>> await user.update(name='Saba', age=19)
            or
            >>> await user.update({'name': 'Saba'}, age=19)
            or
            >>> await user.update({'name': 'Saba', 'age': 19})
        """
        await super().update(_update, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def update_one(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> bool:
        """
        Update a single document matching the filter.

        Example:
        -------
            >>> from app.models import User

            >>> await User.update_one({'id': 1}, age=18, name='Ali')
            or
            >>> await User.update_one({'id': 1}, {'age': 18, 'name': 'Ali'})
            or
            >>> await User.update_one({'id': 1}, {'age': 18}, name='Ali')
        """
        return await super().update_one(_filter, _update, **kwargs)

    @classmethod
    @check_connection
    @log_query
    async def update_many(cls, _filter: dict, _update: dict | None = None, /, **kwargs) -> int:
        """
        Update one or more documents that match the filter.

        Example:
        -------
            >>> from app.models import User

            >>> await User.update_many({'name': 'Saba'}, age=18, name='Ali')
            or
            >>> await User.update_many({'name': 'Saba'}, {'age': 18, 'name': 'Ali'})
            or
            >>> await User.update_many({'name': 'Saba'}, {'age': 18}, name='Ali')
        """
        return await super().update_many(_filter, _update, **kwargs)

    # # # # # Other # # # # #
    @classmethod
    async def all(cls) -> list[Self] | Cursor:
        """
        Alias of find() without args

        Example:
        -------
            >>> from app.models import User

            >>> await User.all()
        """
        return await cls.find()

    @classmethod
    async def find_one_or_insert(cls, _filter: dict | None = None, /, **kwargs) -> tuple[Self, bool]:
        """
        Get a single document from the database.
        or
        Insert a single document.

        Example:
        -------
            >>> from app.models import User

            >>> await User.find_one_or_insert(age=18, name='Ali')
            or
            >>> await User.find_one_or_insert({'age': 18, 'name': 'Ali'})
            or
            >>> await User.find_one_or_insert({'age': 18}, name='Ali')
        """
        if obj := await cls.find_one(_filter, **kwargs):
            return obj, False
        return await cls.insert_one(_filter, **kwargs), True

    @classmethod
    async def find_one_or_raise(cls, _filter: dict | None = None, /, **kwargs) -> Self:
        """
        Example:
        -------
            >>> from app.models import User

            >>> await User.find_one_or_raise(age=18, name='Ali')
            or
            >>> await User.find_one_or_raise({'age': 18, 'name': 'Ali'})
            or
            >>> await User.find_one_or_raise({'age': 18}, name='Ali')
        """
        if obj := await cls.find_one(_filter, **kwargs):
            return obj

        raise NotFoundAPIError(detail=f'{cls.__name__} Does Not Exist')

    @classmethod
    async def exists(cls, _filter: dict | None = None, /, **kwargs) -> bool:
        """
        Check if document exists in collection or not

        Example:
        -------
            >>> from app.models import User

            >>> await User.exists(age=18, name='Ali')
            or
            >>> await User.exists({'age': 18, 'name': 'Ali'})
            or
            >>> await User.exists({'age': 18}, name='Ali')
        """
        if await cls.count(_filter, **kwargs) > 0:
            return True
        else:
            return False

    async def save(self) -> None:
        """
        Save the document
            If it has `id` --> Update It
            else --> Insert It
        Example:
        -------
            >>> from app.models import User

            # Update
            >>> user = await User.find_one(name='Ali')
            >>> user.name = 'Saba'
            >>> await user.save()
            or
            # Insert
            >>> user = User(name='Ali')
            >>> await user.save()
        """
        document = {
            field: getattr(self, field).model_dump()
            if issubclass(type(getattr(self, field)), BaseModel)
            else getattr(self, field)
            for field in self.model_fields.keys() if field != 'request'
        }

        if self.id:
            await self.update(document)
        else:
            await self.insert_one(document)

    async def reload(self) -> Self:
        new_obj = await self.find_one(id=self.id)
        [setattr(self, f, getattr(new_obj, f)) for f in new_obj.model_fields]
        return self
