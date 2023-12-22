import asyncio
import random
from pathlib import Path
from unittest import TestCase

import faker
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator

from panther import Panther
from panther.configs import config
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


DB_PATH = 'test.pdb'
MIDDLEWARES = [
    ('panther.middlewares.db.DatabaseMiddleware', {'url': f'pantherdb://{DB_PATH}'}),
]


class TestPantherDB(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Panther(__name__, configs=__name__, urls={})

    def setUp(self) -> None:
        for middleware in config['middlewares']:
            asyncio.run(middleware.before(request=None))

    def tearDown(self) -> None:
        for middleware in config['reversed_middlewares']:
            asyncio.run(middleware.after(response=None))
        Path(DB_PATH).unlink()

    # # # Insert
    def test_insert_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == 1
        assert book.name == name
        assert book.pages_count == pages_count

    def test_insert_many(self):
        insert_count = self._insert_many()
        assert insert_count > 1

    # # # FindOne
    def test_find_one_not_found(self):
        # Insert Many
        self._insert_many()

        # Find One
        book = Book.find_one(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    def test_find_one_in_many_when_its_last(self):
        # Insert Many
        insert_count = self._insert_many()

        # Insert One
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        created_book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Find One
        book = Book.find_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == insert_count + 1
        assert book._id == book.id
        assert book.name == name
        assert book.pages_count == pages_count
        assert created_book == book

    def test_find_one_in_many_when_its_middle(self):
        # Insert Many
        insert_count = self._insert_many()

        # Insert One
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        created_book = Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Insert Many
        self._insert_many()

        # Find One
        book = Book.find_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == insert_count + 1
        assert book.name == name
        assert book.pages_count == pages_count
        assert created_book == book

    def test_first(self):
        # Insert Many
        insert_count = self._insert_many()

        # Insert Many With Same Params
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)

        # Find First
        book = Book.first(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == insert_count + 1
        assert book.name == name
        assert book.pages_count == pages_count

    def test_first_not_found(self):
        # Insert Many
        self._insert_many()

        # Find First
        book = Book.first(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    def test_last(self):
        # Insert Many
        self._insert_many()

        # Insert Many With Same Params
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)

        # Find One
        book = Book.last(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == Book.count()
        assert book.name == name
        assert book.pages_count == pages_count

    def test_last_not_found(self):
        self._insert_many()

        # Find Last
        book = Book.last(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    # # # Find
    def test_find(self):
        # Insert Many
        self._insert_many()

        # Insert Many With Specific Name
        name = f.name()
        insert_count = self._insert_many_with_specific_params(name=name)

        # Find
        books = Book.find(name=name)

        assert isinstance(books, list)
        assert len(books) == insert_count
        for book in books:
            assert isinstance(book, Book)
            assert book.name == name

    def test_find_not_found(self):
        # Insert Many
        self._insert_many()

        # Find
        books = Book.find(name='NotFound')
        assert isinstance(books, list)
        assert len(books) == 0

    def test_find_without_filter(self):
        # Insert Many
        insert_count = self._insert_many()

        # Find All
        books = Book.find()

        assert isinstance(books, list)
        assert len(books) == insert_count
        for book in books:
            assert isinstance(book, Book)

    def test_all(self):
        # Insert Many
        insert_count = self._insert_many()

        # Find All
        books = Book.all()

        assert isinstance(books, list)
        assert len(books) == insert_count
        for book in books:
            assert isinstance(book, Book)

    def test_all_not_found(self):
        # Find All
        books = Book.all()

        assert isinstance(books, list)
        assert len(books) == 0

    # # # Count
    def test_count_all(self):
        # Insert Many
        insert_count = self._insert_many()

        # Count All
        books_count = Book.count()

        assert isinstance(books_count, int)
        assert books_count == insert_count

    def test_count_with_filter(self):
        # Insert Many
        self._insert_many()

        # Insert Many With Specific Name
        name = f.name()
        insert_count = self._insert_many_with_specific_params(name=name)

        # Count
        books_count = Book.count(name=name)

        assert isinstance(books_count, int)
        assert books_count == insert_count

    def test_count_not_found(self):
        # Insert Many
        self._insert_many()

        # Count
        books_count = Book.count(name='NotFound')

        assert isinstance(books_count, int)
        assert books_count == 0

    # # # Delete One
    def test_delete_one(self):
        # Insert Many
        self._insert_many()

        # Insert With Specific Name
        name = f.name()
        insert_count = self._insert_many_with_specific_params(name=name)

        # Delete One
        is_deleted = Book.delete_one(name=name)

        assert isinstance(is_deleted, bool)
        assert is_deleted is True

        # Count Them After Deletion
        assert Book.count(name=name) == insert_count - 1

    def test_delete_one_not_found(self):
        # Insert Many
        insert_count = self._insert_many()

        # Delete One
        is_deleted = Book.delete_one(name='_Invalid_Name_')

        assert isinstance(is_deleted, bool)
        assert is_deleted is False

        # Count All
        assert Book.count() == insert_count

    # # # Delete Many
    def test_delete_many(self):
        # Insert Many
        pre_insert_count = self._insert_many()

        # Insert With Specific Name
        name = f.name()
        insert_count = self._insert_many_with_specific_params(name=name)

        # Delete Many
        deleted_count = Book.delete_many(name=name)

        assert isinstance(deleted_count, int)
        assert deleted_count == insert_count

        # Count Them After Deletion
        assert Book.count(name=name) == 0
        assert Book.count() == pre_insert_count

    def test_delete_many_not_found(self):
        # Insert Many
        pre_insert_count = self._insert_many()

        # Delete Many
        name = 'NotFound'
        deleted_count = Book.delete_many(name=name)

        assert isinstance(deleted_count, int)
        assert deleted_count == 0

        # Count Them After Deletion
        assert Book.count(name=name) == 0
        assert Book.count() == pre_insert_count

    # # # Update
    def test_update_one(self):
        # Insert Many
        insert_count = self._insert_many()

        # Insert With Specific Name
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Update One
        new_name = 'New Name'
        is_updated = Book.update_one({'name': name}, name=new_name)

        assert isinstance(is_updated, bool)
        assert is_updated is True

        book = Book.find_one(name=new_name)
        assert isinstance(book, Book)
        assert book.author == author
        assert book.pages_count == pages_count

        # Count Them After Update
        assert Book.count(name=name) == 0
        assert Book.count() == insert_count + 1

    def test_update_one_not_found(self):
        # Insert Many
        insert_count = self._insert_many()

        # Update One
        new_name = 'New Name'
        is_updated = Book.update_one({'name': 'NotFound'}, name=new_name)

        assert isinstance(is_updated, bool)
        assert is_updated is False

        book = Book.find_one(name=new_name)
        assert book is None

        # Count Them After Update
        assert Book.count() == insert_count

    # # # Update Many
    def test_update_many(self):
        # Insert Many
        pre_insert_count = self._insert_many()

        # Insert With Specific Name
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        insert_count = self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)

        # Update Many
        new_name = 'New Name'
        updated_count = Book.update_many({'name': name}, name=new_name)

        assert isinstance(updated_count, int)
        assert updated_count == insert_count

        books = Book.find(name=new_name)
        assert isinstance(books, list)
        assert len(books) == updated_count == insert_count
        for book in books:
            assert book.author == author
            assert book.pages_count == pages_count

        # Count Them After Update
        assert Book.count() == pre_insert_count + insert_count

    def test_update_many_not_found(self):
        # Insert Many
        insert_count = self._insert_many()

        # Update Many
        new_name = 'New Name'
        updated_count = Book.update_many({'name': 'NotFound'}, name=new_name)

        assert isinstance(updated_count, int)
        assert updated_count == 0

        book = Book.find_one(name=new_name)
        assert book is None

        # Count Them After Update
        assert Book.count() == insert_count

    @classmethod
    def _insert_many(cls) -> int:
        insert_count = random.randint(2, 10)

        for _ in range(insert_count):
            Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        return insert_count

    @classmethod
    def _insert_many_with_specific_params(
            cls,
            name: str = f.name(),
            author: str = f.name(),
            pages_count: int = random.randint(0, 10)
    ) -> int:
        insert_count = random.randint(2, 10)

        for _ in range(insert_count):
            Book.insert_one(name=name, author=author, pages_count=pages_count)

        return insert_count
