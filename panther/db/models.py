from datetime import datetime

import bson
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries import Query


class Model(PydanticBaseModel, Query):
    id: str | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value: str | int | bson.ObjectId) -> str:
        if isinstance(value, int):
            pass

        elif isinstance(value, str):
            try:
                bson.ObjectId(value)
            except bson.objectid.InvalidId as e:
                msg = 'Invalid ObjectId'
                raise ValueError(msg) from e

        elif not isinstance(value, bson.ObjectId):
            msg = 'ObjectId required'
            raise ValueError(msg) from None

        return str(value)

    @property
    def _id(self) -> int | bson.ObjectId | None:
        if config['query_engine'].__name__ == 'BasePantherDBQuery':
            return int(self.id)
        else:
            return bson.ObjectId(self.id) if self.id else None

    def dict(self, *args, **kwargs) -> dict:
        return self.model_dump(*args, **kwargs)


class BaseUser(Model):
    first_name: str = Field('', max_length=64)
    last_name: str = Field('', max_length=64)
    last_login: datetime = None

    def update_last_login(self) -> None:
        self.update(last_login=datetime.now())
