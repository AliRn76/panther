from typing import Self
from pydantic import ValidationError

from panther.db.connection import db
from panther.db.utils import merge_dicts
from panther.exceptions import DBException


class BasePantherDBQuery:

    @classmethod
    def validate_data(cls, data: dict, is_updating: bool = False) -> Self | None:
        """
        *. Validate the input of user with its class
        *. If is_updating is True & exception happens but the message was empty
                Then return nothing (we don't need the obj on update())
                & we don't have access to the obj after exception ...
        """
        try:
            obj = cls(**data)
        except ValidationError as validation_error:
            error = ', '.join(
                '{field}="{error}"'.format(field=e['loc'][0], error=e['msg'])
                for e in validation_error.errors() if not is_updating or e['type'] != 'value_error.missing')
            if error:
                message = f'{cls.__name__}({error})'
                raise DBException(message)
        else:
            return obj

    @classmethod
    def _merge(cls, *args) -> dict:
        # TODO: Convert "id" to "_id"
        return merge_dicts(*args)

    # # # # # Find # # # # #
    @classmethod
    def find_one(cls, _data: dict = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).first(**cls._merge(_data, kwargs)):
            return cls(**document)

    @classmethod
    def find(cls, _data: dict = None, /, **kwargs) -> list[Self]:
        documents = db.session.collection(cls.__name__).find(**cls._merge(_data, kwargs))
        return [cls(**document) for document in documents]

    # # # # # Insert # # # # #
    @classmethod
    def insert_one(cls, _data: dict = None, **kwargs) -> Self:
        obj = cls.validate_data(kwargs)
        obj.id = db.session.collection(cls.__name__).insert_one(**cls._merge(_data, kwargs))['_id']
        return obj

    @classmethod
    def insert_many(cls, _data: dict = None, /, **kwargs):
        raise DBException('increment() is not supported while using SlarkDB.')

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
        self.validate_data(kwargs, is_updating=True)
        db.session.collection(self.__class__.__name__).update_one({'_id': self.id}, **kwargs)

    @classmethod
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> bool:
        return db.session.collection(cls.__name__).update_one(_filter, **cls._merge(_data, kwargs))

    @classmethod
    def update_many(cls, _filter, _data: dict = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).update_many(_filter, **cls._merge(_data, kwargs))

    # # # # # Other # # # # #
    @classmethod
    def first(cls, _data: dict = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).first(**cls._merge(_data, kwargs)):
            return cls(**document)

    @classmethod
    def last(cls, _data: dict = None, /, **kwargs) -> Self | None:
        if document := db.session.collection(cls.__name__).last(**cls._merge(_data, kwargs)):
            return cls(**document)

    @classmethod
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        return db.session.collection(cls.__name__).count(**cls._merge(_data, kwargs))
