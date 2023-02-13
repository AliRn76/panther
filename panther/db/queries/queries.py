from bson.objectid import ObjectId

from panther.configs import config
from panther.db.queries.mongo_queries import BaseMongoDBQuery
from panther.db.queries.tinydb_queries import BaseTinyDBQuery

BaseQuery = BaseTinyDBQuery if config['db_engine'] == 'tinydb' else BaseMongoDBQuery

__all__ = (
    'Query',
)


class Query(BaseQuery):

    @classmethod
    def get_one(cls, _data: dict = None, /, **kwargs):
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.get_one(id=id)
            elif TinyDB:
                >>> User.get_one(id=id)
        """
        return super().get_one(_data, **kwargs)

    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            >>> from example.app.models import User
            if MongoDB:
                >>> User.count(name='ali', age=24)
            elif TinyDB:
                ...
        """
        return super().count(_data, **kwargs)

    @classmethod
    def list(cls, _data: dict = None, /, **kwargs):
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.list({'state': {'$eq': 'Confirmed'}}, name='ali', age=24)
            elif TinyDB:
                >>> User.list(name='ali', age=24)
        """
        return super().list(_data, **kwargs)

    @classmethod
    def create(cls, _data: dict = None, **kwargs) -> ObjectId:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.create(name='ali', age=24, ...)
            elif TinyDB:
                >>> User.create(name='ali', age=24, ...)
        """
        return super().create(_data, **kwargs)

    def delete(self) -> bool:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> user = User.get_one(name='ali')
                >>> user.delete()
            elif TinyDB:
                ...
        """
        return super().delete()

    @classmethod
    def delete_one(cls, **kwargs) -> bool:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.delete_one(id=id)
            elif TinyDB:
                ...
        """
        return super().delete_one(**kwargs)

    @classmethod
    def delete_many(cls, **kwargs) -> int:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.delete_many(name='ali')
            elif TinyDB:
                ...
        """
        return super().delete_many(**kwargs)

    def update(self, **kwargs) -> dict:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> user = User.get_one(name='ali')
                >>> user.update(name='tom')
            elif TinyDB:
                ...
        """
        return super().update(**kwargs)

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> dict:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.update_one({'id': id}, name='ali')
                >>> User.update_one({'id': id}, {'name': 'ali', 'age': 25})
            elif TinyDB:
                ...
        """
        return super().update_one(_filter, _data, **kwargs)

    @classmethod
    def update_many(cls, _filter, **kwargs) -> dict:
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.update_many({'name': 'mohsen'}, name='ali')
            elif TinyDB:
                ...
        """
        return super().update_many(_filter, **kwargs)

    @classmethod
    def increment(cls, _filter, **kwargs):
        """
        example:
            >>> from example.app.models import User
            if MongoDB:
                >>> User.increment({'priority': {'$gt': ad.priority}}, score=1)
            elif TinyDB:
                ...
        * it will increment score by 1
        """
        return super().increment(_filter, **kwargs)
