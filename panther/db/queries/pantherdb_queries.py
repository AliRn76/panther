from sys import version_info

from panther.db.connection import db
from panther.db.utils import merge_dicts, prepare_id_for_query

if version_info.minor >= 11:
    from typing import Self
else:
    from typing import TypeVar
    Self = TypeVar('Self', bound='BasePantherDBQuery')


class BasePantherDBQuery:

    @classmethod
    def _merge(cls, *args) -> dict:
        prepare_id_for_query(*args)
        return merge_dicts(*args)

    # # # # # Find # # # # #
    @classmethod
    def find_one(cls, _data: dict = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).find_one(**cls._merge(_data, kwargs)):
            return cls.create_model_instance(document=document)

    @classmethod
    def find(cls, _data: dict = None, /, **kwargs) -> list[Self]:
        documents = db.session.collection(cls.__name__).find(**cls._merge(_data, kwargs))
        return [cls.create_model_instance(document=document) for document in documents]

    # # # # # Insert # # # # #
    @classmethod
    def insert_one(cls, _data: dict = None, **kwargs) -> Self:
        document = db.session.collection(cls.__name__).insert_one(**cls._merge(_data, kwargs))
        return cls.create_model_instance(document=document)

    # # # # # Delete # # # # #
    def delete(self) -> None:
        db.session.collection(self.__class__.__name__).delete_one(_id=self.id)

    @classmethod
    def delete_one(cls, _data: dict = None, /, **kwargs) -> bool:
        return db.session.collection(cls.__name__).delete_one(**cls._merge(_data, kwargs))

    @classmethod
    def delete_many(cls, _data: dict = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).delete_many(**cls._merge(_data, kwargs))

    # # # # # Update # # # # #
    def update(self, **kwargs) -> None:
        for field, value in kwargs.items():
            setattr(self, field, value)
        db.session.collection(self.__class__.__name__).update_one({'_id': self.id}, **kwargs)

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> bool:
        prepare_id_for_query(_filter)
        return db.session.collection(cls.__name__).update_one(_filter, **cls._merge(_data, kwargs))

    @classmethod
    def update_many(cls, _filter, _data: dict = None, /, **kwargs) -> int:
        prepare_id_for_query(_filter)
        return db.session.collection(cls.__name__).update_many(_filter, **cls._merge(_data, kwargs))

    # # # # # Other # # # # #
    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).count(**cls._merge(_data, kwargs))
