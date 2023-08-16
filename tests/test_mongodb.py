from unittest import TestCase

import bson
import faker
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.queries.mongodb_queries import BaseMongoDBQuery

f = faker.Faker()


class Model(PydanticBaseModel):
    id: str | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        if isinstance(value, str):
            try:
                bson.ObjectId(value)
            except bson.objectid.InvalidId:
                raise ValueError('Invalid ObjectId')
        elif not isinstance(value, bson.ObjectId):
            raise TypeError('ObjectId required')
        return str(value)

    @property
    def _id(self):
        return bson.ObjectId(self.id) if self.id else None


class Book(Model, BaseMongoDBQuery):
    name: str
    author: str
    pages_count: int


class TestPantherDB(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config['db_engine'] = 'mongodb'

    @classmethod
    def tearDownClass(cls) -> None:
        config['db_engine'] = ''
