import os
import faker
import random
from unittest import TestCase
from pydantic import field_validator, Field, BaseModel as PydanticBaseModel

from panther.configs import config
from panther.db.connection import DBSession
from panther.db.queries.pantherdb_queries import BasePantherDBQuery


f = faker.Faker()


class Model(PydanticBaseModel):
    id: int | None = Field(None, validation_alias='_id')

    @field_validator('id', mode='before')
    def validate_id(cls, value):
        return value

    @property
    def _id(self):
        return self.id


class Book(Model, BasePantherDBQuery):
    name: str
    author: str
    pages_count: int


class TestPantherDB(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config['db_engine'] = 'pantherdb'
        DBSession(db_url=f'pantherdb://database.pdb')

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove('database.pdb')

    def test_insert_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        self.assertIsInstance(book, Book)
        self.assertEqual(book.id, 1)
        self.assertEqual(book.name, name)
        self.assertEqual(book.pages_count, pages_count)
