from __future__ import annotations

from sys import version_info

from panther.utils import run_coroutine

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

    def __aiter__(self) -> Self:
        return self

    def __iter__(self) -> Self:
        return self

    async def next(self) -> Self:
        return await self.cls._create_model_instance(document=super().next())

    async def __anext__(self) -> Self:
        try:
            return await self.cls._create_model_instance(document=super().next())
        except StopIteration:
            raise StopAsyncIteration

    def __next__(self) -> Self:
        try:
            return run_coroutine(self.cls._create_model_instance(document=super().next()))
        except StopIteration:
            raise

    def __getitem__(self, index: int | slice) -> Cursor[Self] | Self:
        document = super().__getitem__(index)
        if isinstance(document, dict):
            return run_coroutine(self.cls._create_model_instance(document=document))
        return document
