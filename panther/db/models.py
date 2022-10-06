from bson import ObjectId
from pydantic import Field
from typing import Optional
from bson.errors import BSONError
from panther.db.queries import Query
from pydantic.main import BaseModel as PydanticBaseModel


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


class BaseModel(PydanticBaseModel, Query):
    id: Optional[BsonObjectId] = Field(alias='_id')

    @property
    def _id(self):
        return ObjectId(self.id) if self.id else None


class User(BaseModel):
    first_name: str | None
    last_name: str | None

