import contextlib
import os
from datetime import datetime

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries import Query
from panther.utils import scrypt, URANDOM_SIZE, timezone_now

with contextlib.suppress(ImportError):
    # Only required if user wants to use mongodb
    import bson


class Model(PydanticBaseModel, Query):
    def __init_subclass__(cls, **kwargs):
        if cls.__module__ == 'panther.db.models' and cls.__name__ == 'BaseUser':
            return
        config.MODELS.append(cls)

    id: str | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value) -> str:
        if config.DATABASE.__class__.__name__ == 'MongoDBConnection':
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
        if config.DATABASE.__class__.__name__ == 'MongoDBConnection':
            return bson.ObjectId(self.id) if self.id else None
        return self.id

    def dict(self, *args, **kwargs) -> dict:
        return self.model_dump(*args, **kwargs)


class BaseUser(Model):
    password: str = Field('', max_length=64)
    last_login: datetime | None = None
    date_created:  datetime | None = Field(default_factory=timezone_now)

    async def update_last_login(self) -> None:
        await self.update(last_login=timezone_now())

    async def login(self) -> dict:
        """Return dict of access and refresh token"""
        return config.AUTHENTICATION.login(self.id)

    async def logout(self) -> dict:
        return await config.AUTHENTICATION.logout(self._auth_token)

    def set_password(self, password: str):
        """
        URANDOM_SIZE = 16 char -->
            salt = 16 bytes
            salt.hex() = 32 char
            derived_key = 32 char
        """
        salt = os.urandom(URANDOM_SIZE)
        derived_key = scrypt(password=password, salt=salt, digest=True)

        self.password = f'{salt.hex()}{derived_key}'

    def check_password(self, new_password: str) -> bool:
        size = URANDOM_SIZE * 2
        salt = self.password[:size]
        stored_hash = self.password[size:]
        derived_key = scrypt(password=new_password, salt=bytes.fromhex(salt), digest=True)

        return derived_key == stored_hash
