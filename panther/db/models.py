from sqlalchemy.orm import declarative_base
from panther.db.queries import Query


Base = declarative_base()


class BaseModel(Base, Query):
    __abstract__ = True
