from bson import ObjectId
from pydantic import Field
from typing import Optional
from bson.errors import BSONError
from sqlalchemy.orm import declarative_base
from pydantic.main import BaseModel as PydanticBaseModel

from panther.db.queries import MongoQuery, SQLiteQuery
from panther.configs import config


Base = declarative_base()


class BsonObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            try:
                ObjectId(v)
            except BSONError:
                raise TypeError('Invalid ObjectId')
        elif not isinstance(v, ObjectId):
            raise TypeError('ObjectId required')
        return str(v)


class MongoBaseModel(PydanticBaseModel, MongoQuery):
    id: Optional[BsonObjectId] = Field(alias='_id')


class SQLBaseModel(Base, SQLiteQuery):
    __abstract__ = True

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


if config['db_engine'] == 'mongodb':
    BaseModel = MongoBaseModel
else:
    BaseModel = SQLBaseModel
