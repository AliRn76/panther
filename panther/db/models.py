import bson
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries import Query

if config['db_engine'] == 'pantherdb':
    IDType = int
else:
    IDType = str


class Model(PydanticBaseModel, Query):
    id: IDType | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        if IDType is str:
            if isinstance(value, str):
                try:
                    bson.ObjectId(value)
                except bson.objectid.InvalidId:
                    raise ValueError('Invalid ObjectId')
            elif not isinstance(value, bson.ObjectId):
                raise ValueError('ObjectId required')
            value = str(value)
        return value

    @property
    def _id(self):
        if IDType is int:
            return self.id
        else:
            return bson.ObjectId(self.id) if self.id else None

    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)


class BaseUser(Model):
    first_name: str | None
    last_name: str | None
