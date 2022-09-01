from panther.db.connection import db
from panther.db.utils import query_logger


# TODO: Complete Queries and Add Docs
class BaseSQLiteQuery:

    @classmethod
    @query_logger
    def get_one(cls, **kwargs):
        return db.session.query(cls).filter_by(**kwargs).first()

    @classmethod
    @query_logger
    def create(cls, body: dict = None, *args, **kwargs):
        """ You can pass data as dict & as kwargs """
        if body:
            obj = cls(**body)
        else:
            obj = cls(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    @query_logger
    def update(self, *args, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                setattr(self, field, value)
        db.session.commit()
        return self

    @classmethod
    @query_logger
    def list(cls, *args, **kwargs):
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

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.get_one(**kwargs)
        if obj:
            return obj
        else:
            return cls.create(**kwargs)
