from sqlalchemy.orm import declarative_base
from panther.db.queries import Query


Base = declarative_base()


# TODO: Make BaseModel dynamic with db.name ...
class BaseModel(Base, Query):
    __abstract__ = True

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

