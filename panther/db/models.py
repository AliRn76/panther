import bson
from pydantic import Field
from pydantic.main import BaseModel as PydanticBaseModel

from panther.configs import config
from panther.db.queries import Query


class BsonObjectId(bson.ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            try:
                bson.ObjectId(v)
            except Exception:
                raise TypeError('Invalid ObjectId')
        elif not isinstance(v, bson.ObjectId):
            raise TypeError('ObjectId required')
        return str(v)


if config['db_engine'] == 'pantherdb':
    IDType = int
else:
    IDType = BsonObjectId


class Model(PydanticBaseModel, Query):
    id: IDType | None = Field(alias='_id')

    @property
    def _id(self):
        if IDType is int:
            return self.id
        else:
            return bson.ObjectId(self.id) if self.id else None


class User(Model):
    first_name: str | None
    last_name: str | None
