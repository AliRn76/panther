from panther.logger import logger

from panther.db.connection import db
from panther.db.utils import query_logger


class Query:
    # # # Main

    @classmethod
    @query_logger
    def get_one(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs).first()

    @classmethod
    @query_logger
    def create(cls, body: dict = None, **kwargs):
        """ You can pass data as dict & as kwargs """
        logger.info('Query create')
        if body:
            obj = cls(**body)
        else:
            obj = cls(**kwargs)
        logger.info('Query after obj')
        print(f'{db = }')
        print(f'{dir(db) = }')
        print(f'{db.session = }')
        db.session.add(obj)
        logger.info('Query after db.session.add')
        return obj

    @classmethod
    @query_logger
    def list(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs)

    @classmethod
    @query_logger
    def delete(cls, commit=True, **kwargs) -> bool:
        """ return boolean --> True=Deleted, False=NotFound  """
        objs = cls.list(**kwargs)
        if not objs.first():
            return False
        objs.delete()
        if commit:
            db.session.commit()
        return True

    # # # Advanced

    @classmethod
    def create_and_commit(cls, body: dict = None, **kwargs):
        """ You can pass data as dict & as kwargs """
        obj = cls.create(body, **kwargs)
        db.session.commit()
        return obj

    @classmethod
    def create_and_flush(cls, body: dict = None, **kwargs):
        """ You can pass data as dict & as kwargs """
        obj = cls.create(body, **kwargs)
        db.session.flush()
        return obj
