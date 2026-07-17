from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterator
from sys import version_info

from panther.db.cursor import Cursor

if version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar

    Self = TypeVar('Self', bound='BaseQuery')


class BaseQuery:
    @classmethod
    @abstractmethod
    async def find_one(cls, *args, **kwargs) -> Self | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def find(cls, *args, **kwargs) -> list[Self] | Cursor:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def first(cls, *args, **kwargs) -> Self | None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def last(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def aggregate(cls, *args, **kwargs) -> Iterator[dict]:
        raise NotImplementedError

    # # # # # Count # # # # #
    @classmethod
    @abstractmethod
    async def count(cls, *args, **kwargs) -> int:
        raise NotImplementedError

    # # # # # Insert # # # # #
    @classmethod
    @abstractmethod
    async def insert_one(cls, *args, **kwargs) -> Self:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def insert_many(cls, *args, **kwargs) -> list[Self]:
        raise NotImplementedError

    # # # # # Delete # # # # #
    @abstractmethod
    async def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def delete_one(cls, *args, **kwargs) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def delete_many(cls, *args, **kwargs) -> int:
        raise NotImplementedError

    # # # # # Update # # # # #
    @abstractmethod
    async def update(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def update_one(cls, *args, **kwargs) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    async def update_many(cls, *args, **kwargs) -> int:
        raise NotImplementedError
