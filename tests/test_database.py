import random
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

import faker
import pytest

from panther import Panther
from panther.db import Model
from panther.db.connections import db
from panther.db.cursor import Cursor as MongoCursor
from pantherdb import Cursor as PantherDBCursor

f = faker.Faker()


class Book(Model):
    name: str
    author: str
    pages_count: int


class _BaseDatabaseTestCase:

    # # # Insert
    async def test_insert_one(self):
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        book = await Book.insert_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id
        assert book.name == name
        assert book.pages_count == pages_count

    async def test_insert_many_with_insert_one(self):
        insert_count = await self._insert_many()
        assert insert_count > 1

    async def test_insert_many(self):
        insert_count = random.randint(2, 10)
        data = [
            {'name': f.name(), 'author': f.name(), 'pages_count': random.randint(0, 10)}
            for _ in range(insert_count)
        ]
        books = await Book.insert_many(data)
        inserted_books = [
            {'_id': book._id, 'name': book.name, 'author': book.author, 'pages_count': book.pages_count}
            for book in books
        ]
        assert len(books) == insert_count
        assert data == inserted_books

    # # # FindOne
    async def test_find_one_not_found(self):
        # Insert Many
        await self._insert_many()

        # Find One
        book = await Book.find_one(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    async def test_find_one_in_many_when_its_last(self):
        # Insert Many
        await self._insert_many()

        # Insert One
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        created_book = await Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Find One
        book = await Book.find_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id
        assert str(book._id) == str(book.id)
        assert book.name == name
        assert book.pages_count == pages_count
        assert created_book == book

    async def test_find_one_in_many_when_its_middle(self):
        # Insert Many
        await self._insert_many()

        # Insert One
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        created_book = await Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Insert Many
        await self._insert_many()

        # Find One
        book = await Book.find_one(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id
        assert book.name == name
        assert book.pages_count == pages_count
        assert created_book == book

    async def test_first(self):
        # Insert Many
        await self._insert_many()

        # Insert Many With Same Params
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        await self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)

        # Find First
        book = await Book.first(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id
        assert book.name == name
        assert book.pages_count == pages_count

    async def test_first_not_found(self):
        # Insert Many
        await self._insert_many()

        # Find First
        book = await Book.first(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    async def test_last(self):
        # Insert Many
        await self._insert_many()

        # Insert Many With Same Params
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        await self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)
        last_obj = await Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Find One
        book = await Book.last(name=name, author=author, pages_count=pages_count)

        assert isinstance(book, Book)
        assert book.id == last_obj.id
        assert book.name == name
        assert book.pages_count == pages_count

    async def test_last_not_found(self):
        await self._insert_many()

        # Find Last
        book = await Book.last(name='NotFound', author='NotFound', pages_count=0)

        assert book is None

    # # # Find
    async def test_find(self):
        # Insert Many
        await self._insert_many()

        # Insert Many With Specific Name
        name = f.name()
        insert_count = await self._insert_many_with_specific_params(name=name)

        # Find
        books = await Book.find(name=name)
        _len = sum(1 for _ in books)

        if self.__class__.__name__ == 'TestMongoDB':
            assert isinstance(books, MongoCursor)
        else:
            assert isinstance(books, PantherDBCursor)
        assert _len == insert_count
        for book in books:
            assert isinstance(book, Book)
            assert book.name == name

    async def test_find_not_found(self):
        # Insert Many
        await self._insert_many()

        # Find
        books = await Book.find(name='NotFound')
        _len = sum(1 for _ in books)

        if self.__class__.__name__ == 'TestMongoDB':
            assert isinstance(books, MongoCursor)
        else:
            assert isinstance(books, PantherDBCursor)
        assert _len == 0

    async def test_find_without_filter(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Find All
        books = await Book.find()
        _len = sum(1 for _ in books)

        if self.__class__.__name__ == 'TestMongoDB':
            assert isinstance(books, MongoCursor)
        else:
            assert isinstance(books, PantherDBCursor)
        assert _len == insert_count
        for book in books:
            assert isinstance(book, Book)

    async def test_all(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Find All
        books = await Book.all()
        _len = sum(1 for _ in books)

        if self.__class__.__name__ == 'TestMongoDB':
            assert isinstance(books, MongoCursor)
        else:
            assert isinstance(books, PantherDBCursor)

        assert _len == insert_count
        for book in books:
            assert isinstance(book, Book)

    async def test_aggregation(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Find All with aggregate
        books = await Book.aggregate([])
        _len = sum(1 for _ in books)

        assert isinstance(books, list)

        assert _len == insert_count
        for book in books:
            assert isinstance(book, dict)
            assert {*book.keys()} == {'_id', 'name', 'author', 'pages_count'}

    # # # Count
    async def test_count_all(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Count All
        books_count = await Book.count()

        assert isinstance(books_count, int)
        assert books_count == insert_count

    async def test_count_with_filter(self):
        # Insert Many
        await self._insert_many()

        # Insert Many With Specific Name
        name = f.name()
        insert_count = await self._insert_many_with_specific_params(name=name)

        # Count
        books_count = await Book.count(name=name)

        assert isinstance(books_count, int)
        assert books_count == insert_count

    async def test_count_not_found(self):
        # Insert Many
        await self._insert_many()

        # Count
        books_count = await Book.count(name='NotFound')

        assert isinstance(books_count, int)
        assert books_count == 0

    # # # Delete One
    async def test_delete_one(self):
        # Insert Many
        await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        insert_count = await self._insert_many_with_specific_params(name=name)

        # Delete One
        is_deleted = await Book.delete_one(name=name)

        assert isinstance(is_deleted, bool)
        assert is_deleted is True

        # Count Them After Deletion
        assert await Book.count(name=name) == insert_count - 1

    async def test_delete_self(self):
        # Insert Many
        await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        insert_count = await self._insert_many_with_specific_params(name=name)
        # Delete One
        book = await Book.find_one(name=name)
        await book.delete()
        # Count Them After Deletion
        assert await Book.count(name=name) == insert_count - 1

    async def test_delete_one_not_found(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Delete One
        is_deleted = await Book.delete_one(name='_Invalid_Name_')

        assert isinstance(is_deleted, bool)
        assert is_deleted is False

        # Count All
        assert await Book.count() == insert_count

    # # # Delete Many
    async def test_delete_many(self):
        # Insert Many
        pre_insert_count = await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        insert_count = await self._insert_many_with_specific_params(name=name)

        # Delete Many
        deleted_count = await Book.delete_many(name=name)

        assert isinstance(deleted_count, int)
        assert deleted_count == insert_count

        # Count Them After Deletion
        assert await Book.count(name=name) == 0
        assert await Book.count() == pre_insert_count

    async def test_delete_many_not_found(self):
        # Insert Many
        pre_insert_count = await self._insert_many()

        # Delete Many
        name = 'NotFound'
        deleted_count = await Book.delete_many(name=name)

        assert isinstance(deleted_count, int)
        assert deleted_count == 0

        # Count Them After Deletion
        assert await Book.count(name=name) == 0
        assert await Book.count() == pre_insert_count

    # # # Update
    async def test_update_one(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        await Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Update One
        new_name = 'New Name'
        is_updated = await Book.update_one({'name': name}, name=new_name)

        assert isinstance(is_updated, bool)
        assert is_updated is True

        book = await Book.find_one(name=new_name)
        assert isinstance(book, Book)
        assert book.author == author
        assert book.pages_count == pages_count

        # Count Them After Update
        assert await Book.count(name=name) == 0
        assert await Book.count() == insert_count + 1

    async def test_update_self(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        await Book.insert_one(name=name, author=author, pages_count=pages_count)

        # Update One
        book = await Book.find_one(name=name)
        new_name = 'New Name'
        await book.update(name=new_name)

        assert book.name == new_name
        assert book.author == author

        book = await Book.find_one(name=new_name)
        assert isinstance(book, Book)
        assert book.author == author
        assert book.pages_count == pages_count

        # Count Them After Update
        assert await Book.count(name=name) == 0
        assert await Book.count() == insert_count + 1

    async def test_update_one_not_found(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Update One
        new_name = 'New Name'
        is_updated = await Book.update_one({'name': 'NotFound'}, name=new_name)

        assert isinstance(is_updated, bool)
        assert is_updated is False

        book = await Book.find_one(name=new_name)
        assert book is None

        # Count Them After Update
        assert await Book.count() == insert_count

    # # # Update Many
    async def test_update_many(self):
        # Insert Many
        pre_insert_count = await self._insert_many()

        # Insert With Specific Name
        name = f.name()
        author = f.name()
        pages_count = random.randint(0, 10)
        insert_count = await self._insert_many_with_specific_params(name=name, author=author, pages_count=pages_count)

        # Update Many
        new_name = 'New Name'
        updated_count = await Book.update_many({'name': name}, name=new_name)

        assert isinstance(updated_count, int)
        assert updated_count == insert_count

        books = await Book.find(name=new_name)
        _len = sum(1 for _ in books)

        if self.__class__.__name__ == 'TestMongoDB':
            assert isinstance(books, MongoCursor)
        else:
            assert isinstance(books, PantherDBCursor)
        assert _len == updated_count == insert_count
        for book in books:
            assert book.author == author
            assert book.pages_count == pages_count

        # Count Them After Update
        assert await Book.count() == pre_insert_count + insert_count

    async def test_update_many_not_found(self):
        # Insert Many
        insert_count = await self._insert_many()

        # Update Many
        new_name = 'New Name'
        updated_count = await Book.update_many({'name': 'NotFound'}, name=new_name)

        assert isinstance(updated_count, int)
        assert updated_count == 0

        book = await Book.find_one(name=new_name)
        assert book is None

        # Count Them After Update
        assert await Book.count() == insert_count

    @classmethod
    async def _insert_many(cls) -> int:
        insert_count = random.randint(2, 10)

        for _ in range(insert_count):
            await Book.insert_one(name=f.name(), author=f.name(), pages_count=random.randint(0, 10))

        return insert_count

    @classmethod
    async def _insert_many_with_specific_params(
            cls,
            name: str = f.name(),
            author: str = f.name(),
            pages_count: int = random.randint(0, 10)
    ) -> int:
        insert_count = random.randint(2, 10)

        for _ in range(insert_count):
            await Book.insert_one(name=name, author=author, pages_count=pages_count)

        return insert_count


class TestPantherDB(_BaseDatabaseTestCase, IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.PantherDBConnection',
                'path': cls.DB_PATH
            },
        }
        Panther(__name__, configs=__name__, urls={})

    def tearDown(self) -> None:
        Path(self.DB_PATH).unlink()

    async def test_aggregation(self):
        pass


@pytest.mark.mongodb
class TestMongoDB(_BaseDatabaseTestCase, IsolatedAsyncioTestCase):
    DB_NAME = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.MongoDBConnection',
                'host': f'mongodb://127.0.0.1:27017/{cls.DB_NAME}',
            },
        }

    def setUp(self):
        Panther(__name__, configs=__name__, urls={})

    def tearDown(self) -> None:
        db.session.drop_collection('Book')
