from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries import Query


try:
    # Only required if user wants to use mongodb
    import bson
except ImportError:
    pass


class Model(PydanticBaseModel, Query):
    def __init_subclass__(cls, **kwargs):
        if cls.__module__ == 'panther.db.models' and cls.__name__ == 'BaseUser':
            return
        config['models'].append(cls)

    id: str | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value) -> str:
        if config['database'].__class__.__name__ == 'MongoDBConnection':
            if isinstance(value, str):
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
    def _id(self):
        """
        return
            `str` for PantherDB
            `ObjectId` for MongoDB
        """
        if config['database'].__class__.__name__ == 'MongoDBConnection':
            return bson.ObjectId(self.id) if self.id else None
        return self.id

    def dict(self, *args, **kwargs) -> dict:
        return self.model_dump(*args, **kwargs)


class BaseUser(Model):
    first_name: str = Field('', max_length=64)
    last_name: str = Field('', max_length=64)
    last_login: datetime | None = None

    async def update_last_login(self) -> None:
        await self.update(last_login=datetime.now())

    async def login(self) -> dict:
        """Return dict of access and refresh token"""
        await self.update_last_login()
        return config.authentication.login(self.id)

    def logout(self) -> dict:
        return config.authentication.logout(self._auth_token)
