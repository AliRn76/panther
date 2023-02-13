from tinydb import Query

from panther.db.connection import db
from panther.db.utils import merge_dicts, query_logger
from panther.logger import logger


class BaseTinyDBQuery:

    @classmethod
    @query_logger
    def get_one(cls, _data: dict = None, /, **kwargs):
        result = db.session.table(cls.__name__).search(Query().fragment(merge_dicts(_data, kwargs)))
        if len(result) < 1:
            return None
        else:
            return result[0]

    @classmethod
    @query_logger
    def count(cls, _data: dict = None, /, **kwargs) -> int:
        return len(db.session.table(cls.__name__).search(Query().fragment(merge_dicts(_data, kwargs))))

    @classmethod
    @query_logger
    def list(cls, _data: dict = None, /, **kwargs):
        return db.session.table(cls.__name__).search(Query().fragment(merge_dicts(_data, kwargs)))

    @classmethod
    @query_logger
    def create(cls, _data: dict = None, **kwargs) -> int:
        return db.session.table(cls.__name__).insert(merge_dicts(_data, kwargs))

    @query_logger
    def delete(self) -> None:
        logger.critical('delete() is not supported while using TinyDB.')

    @classmethod
    @query_logger
    def delete_one(cls, **kwargs) -> None:
        logger.critical('delete_one() is not supported while using TinyDB.')

    @classmethod
    @query_logger
    def delete_many(cls, _data: dict = None, /, **kwargs) -> int:
        return len(db.session.table(cls.__name__).remove(Query().fragment(kwargs)))

    @query_logger
    def update(self, **kwargs) -> None:
        logger.critical('update() is not supported while using TinyDB.')

    @classmethod
    @query_logger
    def update_one(cls, _filter, _data: dict = None, /, **kwargs) -> None:
        logger.critical('update_one() is not supported while using TinyDB.')

    @classmethod
    @query_logger
    def update_many(cls, _filter, **kwargs) -> None:
        logger.critical('update_many() is not supported while using TinyDB.')

    @classmethod
    @query_logger
    def increment(cls, _filter, **kwargs) -> None:
        logger.critical('increment() is not supported while using TinyDB.')

