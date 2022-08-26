from panther.db.connection import db
from panther.db.utils import query_logger
from panther.exceptions import APIException


class MongoQuery:

    @classmethod
    @query_logger
    def create(cls, klass, body: dict = None, *args, **kwargs):
        """ You can pass data as dict & as kwargs """
        return eval(f'db.session.{klass.__name__}.insert_one(kwargs)')

    @classmethod
    @query_logger
    def list(cls, klass, *args, **kwargs):
        return eval(f'db.session.{klass.__name__}.find(kwargs)')

    # TODO: Continue ...


class SQLiteQuery:
    # # # Main

    @classmethod
    @query_logger
    def get_one(cls, klass, **kwargs):
        return db.session.query(klass).filter_by(**kwargs).first()

    @classmethod
    @query_logger
    def create(cls, klass, body: dict = None, *args, **kwargs):
        """ You can pass data as dict & as kwargs """
        if body:
            obj = klass(**body)
        else:
            obj = klass(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    @query_logger
    def update(self, *args, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        return self

    @classmethod
    @query_logger
    def list(cls, klass, *args, **kwargs):
        return db.session.query(klass).filter_by(**kwargs)

    @classmethod
    @query_logger
    def delete(cls, klass, commit=True, **kwargs) -> bool:
        """ return boolean --> True=Deleted, False=NotFound  """
        objs = klass.list(**kwargs)
        if not objs.first():
            return False
        objs.delete()
        if commit:
            db.session.commit()
        return True

    @classmethod
    @query_logger
    def last(cls, klass, field='id'):
        return db.session.query(klass).order_by(eval(f'klass.{field}.desc()')).first()

    # # # Advanced

    # @classmethod
    # def create_and_commit(cls, body: dict = None, **kwargs):
    #     """ You can pass data as dict & as kwargs """
    #     obj = cls.create(body, **kwargs)
    #     db.session.commit()
    #     return obj

    @classmethod
    def create_and_flush(cls, body: dict = None, **kwargs):
        """ You can pass data as dict & as kwargs """
        obj = cls.create(body, **kwargs)
        db.session.flush()
        return obj

    @query_logger
    def update_and_commit(self, **kwargs):
        self.update(**kwargs)
        db.session.commit()
        return self

    @classmethod
    def get_or_raise(cls, **kwargs):
        obj = cls.get_one(**kwargs)
        if obj:
            return obj
        else:
            raise APIException(detail=f'{cls} Not Found.', status_code=404)

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.get_one(**kwargs)
        if obj:
            return obj
        else:
            return cls.create(**kwargs)


def query_handler(func):
    def wrap(*args, **kwargs):
        if db.name == 'mongodb':
            return eval(f'MongoQuery.{func.__name__}(*args, **kwargs)')
        elif db.name == 'sqlite':
            return eval(f'SQLiteQuery.{func.__name__}(*args, **kwargs)')
        return func(*args, **kwargs)
    return wrap


class Query(object):

    @classmethod
    @query_handler
    def create(cls, body: dict = None, **kwargs):
        """ You can pass data as dict & as kwargs """
        pass

    @classmethod
    @query_handler
    def list(cls, **kwargs):
        """ You can pass data as dict & as kwargs """
        pass
