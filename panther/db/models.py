import contextlib
import os
from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field, WrapValidator, PlainSerializer, BaseModel as PydanticBaseModel

from panther.configs import config
from panther.db.queries import Query
from panther.utils import scrypt, URANDOM_SIZE, timezone_now

with contextlib.suppress(ImportError):
    # Only required if user wants to use mongodb
    import bson


def validate_object_id(value, handler):
    if config.DATABASE.__class__.__name__ != 'MongoDBConnection':
        return str(value)

    if isinstance(value, bson.ObjectId):
        return value

    try:
        return bson.ObjectId(value)
    except Exception as e:
        msg = 'Invalid ObjectId'
        raise ValueError(msg) from e


ID = Annotated[str, WrapValidator(validate_object_id), PlainSerializer(lambda x: str(x), return_type=str)]


class Model(PydanticBaseModel, Query):
    def __init_subclass__(cls, **kwargs):
        if cls.__module__ == 'panther.db.models' and cls.__name__ == 'BaseUser':
            return
        config.MODELS.append(cls)

    id: ID | None = Field(None, validation_alias='_id', alias='_id')

    @property
    def _id(self):
        """
        Returns the actual ID value:
            - For MongoDB: returns ObjectId
            - For PantherDB: returns str
        """
        if config.DATABASE.__class__.__name__ == 'MongoDBConnection':
            return bson.ObjectId(self.id)
        return self.id


class BaseUser(Model):
    username: str
    password: str = Field('', max_length=64)
    last_login: datetime | None = None
    date_created: datetime | None = Field(default_factory=timezone_now)

    USERNAME_FIELD: ClassVar = 'username'

    async def update_last_login(self) -> None:
        await self.update(last_login=timezone_now())

    async def login(self) -> dict:
        """Return dict of access and refresh token"""
        return config.AUTHENTICATION.login(str(self.id))

    async def logout(self) -> dict:
        return await config.AUTHENTICATION.logout(self._auth_token)

    async def set_password(self, password: str):
        """
        URANDOM_SIZE = 16 char -->
            salt = 16 bytes
            salt.hex() = 32 char
            derived_key = 32 char
        """
        salt = os.urandom(URANDOM_SIZE)
        derived_key = scrypt(password=password, salt=salt, digest=True)

        hashed_password = f'{salt.hex()}{derived_key}'
        await self.update(password=hashed_password)

    def check_password(self, password: str) -> bool:
        size = URANDOM_SIZE * 2
        salt = self.password[:size]
        stored_hash = self.password[size:]
        derived_key = scrypt(password=password, salt=bytes.fromhex(salt), digest=True)

        return derived_key == stored_hash
