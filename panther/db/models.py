from sqlalchemy.orm import declarative_base
from panther.db.queries import Query


Base = declarative_base()


class BaseModel(Base, Query):
    __abstract__ = True
    datetime_fields = ()

    def as_dict(self, excluded_fields=()):
        view_model = {}
        for c in self.__table__.columns:
            if c.name in excluded_fields:
                continue
            if c.name in self.datetime_fields:
                view_model[c.name] = getattr(self, c.name).isoformat() if getattr(self, c.name) else None
            else:
                view_model[c.name] = getattr(self, c.name)

        return view_model
