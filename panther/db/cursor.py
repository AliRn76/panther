from __future__ import annotations

from sys import version_info

try:
    from pymongo.cursor import Cursor as _Cursor
except ImportError:
    # This '_Cursor' is not going to be used,
    #   If user really wants to use it,
    #   we are going to force him to install it in `panther.db.connections.MongoDBConnection.init`
    _Cursor = type('_Cursor', (), {})

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseMongoDBQuery')


class Cursor(_Cursor):
    models = {}

    def __init__(self, collection, *args, cls=None, **kwargs):
        # cls.__name__ and collection.name are equal.
        if cls:
            self.models[collection.name] = cls
            self.cls = cls
            self.filter = kwargs['filter']
        else:
            self.cls = self.models[collection.name]
        super().__init__(collection, *args, **kwargs)

    def next(self) -> Self:
        return self.cls._create_model_instance(document=super().next())

    __next__ = next

    def __getitem__(self, index: int | slice) -> Cursor[Self] | Self:
        result = super().__getitem__(index)
        if isinstance(result, dict):
            return self.cls._create_model_instance(document=result)
        return result
