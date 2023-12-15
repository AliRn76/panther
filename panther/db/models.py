from datetime import datetime

import bson
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries import Query

IDType = int if config['db_engine'] == 'pantherdb' else str


class Model(PydanticBaseModel, Query):
    id: IDType | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value: IDType | bson.ObjectId) -> IDType:
        if IDType is str:
            if isinstance(value, str):
                try:
                    bson.ObjectId(value)
                except bson.objectid.InvalidId as e:
                    msg = 'Invalid ObjectId'
                    raise ValueError(msg) from e
            elif not isinstance(value, bson.ObjectId):
                msg = 'ObjectId required'
                raise ValueError(msg) from None
            value = str(value)
        return value

    @property
    def _id(self) -> int | bson.ObjectId | None:
        if IDType is int:
            return self.id
        return bson.ObjectId(self.id) if self.id else None

    def dict(self, *args, **kwargs) -> dict:
        return self.model_dump(*args, **kwargs)


class BaseUser(Model):
    first_name: str = Field('', max_length=64)
    last_name: str = Field('', max_length=64)
    last_login: datetime = None

    def update_last_login(self) -> None:
        self.update(last_login=datetime.now())
