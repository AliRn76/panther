from panther.db.connection import db
from panther.db.utils import query_logger
from panther.exceptions import APIException


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
        if body:
            obj = cls(**body)
        else:
            obj = cls(**kwargs)
        db.session.add(obj)
        return obj

    @query_logger
    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self, field, value)
        return self

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

    @classmethod
    @query_logger
    def last(cls, field='id'):
        return db.session.query(cls).order_by(eval(f'cls.{field}.desc()')).first()

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

    @classmethod
    def get_or_create_and_commit(cls, **kwargs):
        obj = cls.get_one(**kwargs)
        if obj:
            return obj
        else:
            return cls.create_and_commit(**kwargs)
