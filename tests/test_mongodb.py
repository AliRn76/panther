import bson
import faker
import random
from unittest import TestCase
from pydantic import field_validator, Field, BaseModel as PydanticBaseModel

from panther.configs import config
from panther.db.connection import DBSession
from panther.db.queries.mongodb_queries import BaseMongoDBQuery


f = faker.Faker()


class Model(PydanticBaseModel):
    id: str | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        if isinstance(value, str):
            try:
                bson.ObjectId(value)
            except Exception:
                raise ValueError('Invalid ObjectId')
        elif not isinstance(value, bson.ObjectId):
            raise ValueError('ObjectId required')
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
        cls.db = DBSession(db_url=f'mongodb://127.0.0.1:27017/test')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.db.close()

    def test_insert_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        self.assertIsInstance(book, Book)
        self.assertIsNotNone(book.id)
        self.assertEqual(book.name, name)
        self.assertEqual(book.pages_count, pages_count)
