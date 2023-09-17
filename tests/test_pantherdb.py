import random
from pathlib import Path
from unittest import TestCase

import faker
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther.configs import config
from panther.db.connection import DBSession
from panther.db.queries import Query
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


class Book(Model, BasePantherDBQuery, Query):
    name: str
    author: str
    pages_count: int


class TestPantherDB(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config['db_engine'] = 'pantherdb'

    def setUp(self) -> None:
        DBSession(db_url='pantherdb://database.pdb')

    @classmethod
    def tearDownClass(cls) -> None:
        config['db_engine'] = ''

    def tearDown(self) -> None:
        Path('database.pdb').unlink()

    def test_insert_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        self.assertIsInstance(book, Book)
        self.assertEqual(book.id, 1)
        self.assertEqual(book.name, name)
        self.assertEqual(book.pages_count, pages_count)

    def test_find_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        # Insert
        created_book = Book.insert_one(name=name, author=author, pages_count=pages_count)
        # FindOne
        book = Book.find_one(name=name, author=author, pages_count=pages_count)

        self.assertIsInstance(book, Book)
        self.assertEqual(book.id, 1)
        self.assertEqual(book.name, name)
        self.assertEqual(book.pages_count, pages_count)
        self.assertEqual(created_book, book)

    def test_find_one_in_many(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        insert_count = random.randint(2, 10)
        # Insert Many
        for _ in range(insert_count):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))
        created_book = Book.insert_one(name=name, author=author, pages_count=pages_count)
        # FindOne
        book = Book.find_one(name=name, author=author, pages_count=pages_count)

        self.assertIsInstance(book, Book)
        self.assertEqual(book.id, insert_count + 1)
        self.assertEqual(book.name, name)
        self.assertEqual(book.pages_count, pages_count)
        self.assertEqual(created_book, book)

    def test_find(self):
        # Insert Many
        for _ in range(random.randint(2, 10)):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        name = f.name()
        insert_count = random.randint(2, 10)
        for _ in range(insert_count):
            Book.insert_one(name=name, author=f.name(), pages_count=random.randint(0, 10))

        # Find
        books = Book.find(name=name)

        self.assertIsInstance(books, list)
        self.assertEqual(len(books), insert_count)
        book = books[0]
        self.assertIsInstance(book, Book)
        self.assertEqual(book.name, name)

    def test_all(self):
        insert_count = random.randint(2, 10)
        # Insert Many
        for _ in range(insert_count):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        # Find All
        books = Book.find()

        self.assertIsInstance(books, list)
        self.assertEqual(len(books), insert_count)
        book = books[0]
        self.assertIsInstance(book, Book)

    def test_count_all(self):
        insert_count = random.randint(2, 10)
        # Insert Many
        for _ in range(insert_count):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        # Count All
        books_count = Book.count()

        self.assertIsInstance(books_count, int)
        self.assertEqual(books_count, insert_count)

    def test_count_with_filter(self):
        # Insert Many
        for _ in range(random.randint(2, 10)):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        name = f.name()
        insert_count = random.randint(2, 10)
        for _ in range(insert_count):
            Book.insert_one(name=name, author=f.name(), pages_count=random.randint(0, 10))

        # Count
        books_count = Book.count(name=name)

        self.assertIsInstance(books_count, int)
        self.assertEqual(books_count, insert_count)

    def test_delete_one(self):
        # Insert Many
        for _ in range(random.randint(2, 10)):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        name = f.name()
        Book.insert_one(name=name, author=f.name(), pages_count=random.randint(0, 10))

        # Delete One
        is_deleted = Book.delete_one(name=name)

        self.assertIsInstance(is_deleted, bool)
        self.assertTrue(is_deleted)

        # Count Them
        books_count = Book.count(name=name)
        self.assertEqual(books_count, 0)

    def test_delete_one_not_found(self):
        insert_count = random.randint(2, 10)
        # Insert Many
        for _ in range(insert_count):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        # Delete One
        is_deleted = Book.delete_one(name='InvalidName')

        self.assertIsInstance(is_deleted, bool)
        self.assertFalse(is_deleted)

        # Count All
        books_count = Book.count()
        self.assertEqual(books_count, insert_count)
