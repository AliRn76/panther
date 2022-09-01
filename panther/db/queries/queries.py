from bson.objectid import ObjectId
from panther.db.queries.mongo_queries import BaseMongoQuery
from panther.db.queries.sqlite_queries import BaseSQLiteQuery


__all__ = (
    'SQLiteQuery',
    'MongoQuery'
)


class SQLiteQuery(BaseSQLiteQuery):

    @classmethod
    def get_one(cls, **kwargs):
        return super().get_one(**kwargs)

    @classmethod
    def create(cls, body: dict = None, *args, **kwargs):
        return super().create(body, *args, **kwargs)

    def update(self, *args, **kwargs):
        return super().update(*args, **kwargs)

    @classmethod
    def list(cls, *args, **kwargs):
        return super().list(*args, **kwargs)

    @classmethod
    def delete(cls, commit=True, **kwargs) -> bool:
        return super().delete(commit, **kwargs)

    @classmethod
    def last(cls, field='id'):
        return super().last(field)

    @classmethod
    def get_or_create(cls, **kwargs):
        return super().get_or_create(**kwargs)


class MongoQuery(BaseMongoQuery):

    @classmethod
    def get_one(cls, _data: dict = None, /, **kwargs):
        """
        example:
            User.get_one(id=id)
        """
        return super().get_one(_data, **kwargs)

    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        """
        example:
            User.count({'state': {'$eq': 'Confirmed'}}, name='ali', age=24)
        """
        return super().count(_data, **kwargs)

    @classmethod
    def list(cls, _data: dict = None, /, **kwargs):
        """
        example:
            User.list({'state': {'$eq': 'Confirmed'}}, name='ali', age=24)
        """
        return super().list(_data, **kwargs)

    @classmethod
    def create(cls, **kwargs) -> ObjectId:
        """
        example:
            User.create(name='ali', age=24, ...)
        """
        return super().create(**kwargs)

    def delete(self) -> bool:
        """
        example:
            User.delete()
        """
        return super().delete()

    @classmethod
    def delete_one(cls, **kwargs) -> bool:
        """
        example:
            User.delete_one(id=_id)
        """
        return super().delete_one(**kwargs)

    @classmethod
    def delete_many(cls, **kwargs) -> int:
        """
        example:
            User.delete_many(name='ali')
        """
        return super().delete_many(**kwargs)

    def update(self, **kwargs) -> dict:
        """
        example:
            user.update(name='ali')
        """
        return super().update(**kwargs)

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> dict:
        """
        example:
            User.update_one({'id': _id}, name='ali')
        """
        return super().update_one(_filter, _data, **kwargs)

    @classmethod
    def update_many(cls, _filter, **kwargs) -> dict:
        """
        example:
            User.update_many({'name': 'mohsen'}, name='ali')
        """
        return super().update_many(_filter, **kwargs)

    @classmethod
    def increment(cls, _filter, **kwargs):
        """
        example:
            User.increment({'priority': {'$gt': ad.priority}}, score=1)
        * it will increment score by 1
        """
        return super().increment(_filter, **kwargs)
