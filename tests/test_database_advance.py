import asyncio
import contextlib
from pathlib import Path
from typing import List
from unittest import IsolatedAsyncioTestCase

import faker
import pytest
from pydantic import BaseModel

from panther import Panther
from panther.configs import config
from panther.db import Model
from panther.db.connections import db
from panther.exceptions import DatabaseError, NotFoundAPIError

with contextlib.suppress(ImportError):
    # Only required if user wants to use mongodb
    import bson

f = faker.Faker()


class Book(Model):
    name: str


class BookDetail(BaseModel):
    detail: str
    book: Book
    more_books: list[list[Book]]


class Viewer(BaseModel):
    first_name: str


class Library(Model):
    name: str
    books: list[Book]
    viewer: Viewer


class TestBook(Model):
    name: str
    author: str
    pages_count: int


class Author(Model):
    name: str
    books: list[Book]
    books2: List[Book]
    book: Book
    book2: None | Book = None
    book_detail: dict
    our_book_detail: BookDetail


class InvalidModel(Model):
    new_book: dict[str, Book]


class Publisher(Model):
    name: str
    rating: float
    is_active: bool


class _BaseDatabaseTestCase:
    async def test_insert_one(self):
        book = await Book.insert_one(name='my_test')
        author = await Author.insert_one(
            {'name': 'ali'},
            books=[book],
            books2=[book.id, book.model_dump()],
            book=Book(name='test_book1'),
            book2=None,
            book_detail={'book1': book},
            our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
        )

        assert isinstance(book, Book)
        assert book.id
        assert book.name == 'my_test'

        assert author.name == 'ali'
        assert isinstance(author.books, list)
        assert len(author.books) == 1
        assert author.books[0] == book
        assert author.books[0]

        assert isinstance(author.books2, list)
        assert len(author.books2) == 2
        assert author.books2[0] == book
        assert author.books2[1] == book

        assert isinstance(author.book, Book)
        assert author.book.id
        assert author.book.name == 'test_book1'

        assert author.book2 is None

        assert isinstance(author.book_detail, dict)
        assert list(author.book_detail.keys()) == ['book1']
        assert author.book_detail['book1'] == book.id  # Known Issue

        assert isinstance(author.our_book_detail, BookDetail)
        assert author.our_book_detail.detail == 'ok'
        assert author.our_book_detail.book == book
        assert isinstance(author.our_book_detail.more_books, list)
        assert len(author.our_book_detail.more_books) == 1
        assert isinstance(author.our_book_detail.more_books[0], list)
        assert len(author.our_book_detail.more_books[0]) == 2
        assert author.our_book_detail.more_books[0][0] == book
        assert author.our_book_detail.more_books[0][1] == book

    async def test_insert_one_with_model_obj(self):
        book = await Book.insert_one(name='my_test')
        author = await Author.insert_one(
            Author(
                name='ali',
                books=[book],
                books2=[book, book],
                book=Book(name='test_book1'),
                book2=None,
                book_detail={'book1': book},
                our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
            )
        )

        assert isinstance(book, Book)
        assert book.id
        assert book.name == 'my_test'

        assert author.name == 'ali'
        assert isinstance(author.books, list)
        assert len(author.books) == 1
        assert author.books[0] == book
        assert author.books[0]

        assert isinstance(author.books2, list)
        assert len(author.books2) == 2
        assert author.books2[0] == book
        assert author.books2[1] == book

        assert isinstance(author.book, Book)
        assert author.book.id
        assert author.book.name == 'test_book1'

        assert author.book2 is None

        assert isinstance(author.book_detail, dict)
        assert list(author.book_detail.keys()) == ['book1']
        assert author.book_detail['book1'] == book.id  # Known Issue

        assert isinstance(author.our_book_detail, BookDetail)
        assert author.our_book_detail.detail == 'ok'
        assert author.our_book_detail.book == book
        assert isinstance(author.our_book_detail.more_books, list)
        assert len(author.our_book_detail.more_books) == 1
        assert isinstance(author.our_book_detail.more_books[0], list)
        assert len(author.our_book_detail.more_books[0]) == 2
        assert author.our_book_detail.more_books[0][0] == book
        assert author.our_book_detail.more_books[0][1] == book

    async def test_insert_one_with_model_dump(self):
        book = await Book.insert_one(name='my_test')
        author = await Author.insert_one(
            Author(
                name='ali',
                books=[book],
                books2=[book, book],
                book=book,
                book2=None,
                book_detail={'book1': book},
                our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
            ).model_dump()
        )

        assert isinstance(book, Book)
        assert book.id
        assert book.name == 'my_test'

        assert author.name == 'ali'
        assert isinstance(author.books, list)
        assert len(author.books) == 1
        assert author.books[0] == book
        assert author.books[0]

        assert isinstance(author.books2, list)
        assert len(author.books2) == 2
        assert author.books2[0] == book
        assert author.books2[1] == book

        assert isinstance(author.book, Book)
        assert author.book == book

        assert author.book2 is None

        assert isinstance(author.book_detail, dict)
        assert list(author.book_detail.keys()) == ['book1']
        assert author.book_detail['book1'] == book.model_dump()

        assert isinstance(author.our_book_detail, BookDetail)
        assert author.our_book_detail.detail == 'ok'
        assert author.our_book_detail.book == book
        assert isinstance(author.our_book_detail.more_books, list)
        assert len(author.our_book_detail.more_books) == 1
        assert isinstance(author.our_book_detail.more_books[0], list)
        assert len(author.our_book_detail.more_books[0]) == 2
        assert author.our_book_detail.more_books[0][0] == book
        assert author.our_book_detail.more_books[0][1] == book

    async def test_insert_many(self):
        book = await Book.insert_one(name='my_test')
        authors = await Author.insert_many(
            [
                {
                    'name': 'ali',
                    'books': [book],
                    'books2': [book.id, book],
                    'book': Book(name='test_book1'),
                    'book2': None,
                    'book_detail': {'book1': book.model_dump()},
                    'our_book_detail': BookDetail(detail='ok', book=book, more_books=[[book, book]]),
                },
                {
                    'name': 'ali',
                    'books': [book],
                    'books2': [book.id, book],
                    'book': Book(name='test_book2'),
                    'book2': None,
                    'book_detail': {'book1': book.model_dump()},
                    'our_book_detail': BookDetail(detail='ok', book=book, more_books=[[book, book]]),
                },
            ],
        )

        for author in authors:
            assert isinstance(book, Book)
            assert book.id
            assert book.name == 'my_test'

            assert author.name == 'ali'
            assert isinstance(author.books, list)
            assert len(author.books) == 1
            assert author.books[0] == book
            assert author.books[0]

            assert isinstance(author.books2, list)
            assert len(author.books2) == 2
            assert author.books2[0] == book
            assert author.books2[1] == book

            assert isinstance(author.book, Book)
            assert author.book.id
            assert author.book.name in ['test_book1', 'test_book2']

            assert author.book2 is None

            assert isinstance(author.book_detail, dict)
            assert list(author.book_detail.keys()) == ['book1']
            assert author.book_detail['book1'] == book.model_dump()

            assert isinstance(author.our_book_detail, BookDetail)
            assert author.our_book_detail.detail == 'ok'
            assert author.our_book_detail.book == book
            assert isinstance(author.our_book_detail.more_books, list)
            assert len(author.our_book_detail.more_books) == 1
            assert isinstance(author.our_book_detail.more_books[0], list)
            assert len(author.our_book_detail.more_books[0]) == 2
            assert author.our_book_detail.more_books[0][0] == book
            assert author.our_book_detail.more_books[0][1] == book

    async def test_find_one(self):
        book = await Book.insert_one(name='my_test')
        await Author.insert_one(
            name='ali',
            books=[book],
            books2=[book, book],
            book=Book(name='test_book1'),
            book2=None,
            book_detail={'book1': book},
            our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
        )
        author = await Author.find_one(name='ali')

        assert isinstance(book, Book)
        assert book.id
        assert book.name == 'my_test'

        assert author.name == 'ali'
        assert isinstance(author.books, list)
        assert len(author.books) == 1
        assert author.books[0] == book
        assert author.books[0]

        assert isinstance(author.books2, list)
        assert len(author.books2) == 2
        assert author.books2[0] == book
        assert author.books2[1] == book

        assert isinstance(author.book, Book)
        assert author.book.id
        assert author.book.name == 'test_book1'

        assert author.book2 is None

        assert isinstance(author.book_detail, dict)
        assert list(author.book_detail.keys()) == ['book1']
        assert author.book_detail['book1'] == book.id  # Known Issue

        assert isinstance(author.our_book_detail, BookDetail)
        assert author.our_book_detail.detail == 'ok'
        assert author.our_book_detail.book == book
        assert isinstance(author.our_book_detail.more_books, list)
        assert len(author.our_book_detail.more_books) == 1
        assert isinstance(author.our_book_detail.more_books[0], list)
        assert len(author.our_book_detail.more_books[0]) == 2
        assert author.our_book_detail.more_books[0][0] == book
        assert author.our_book_detail.more_books[0][1] == book

    async def test_find(self):
        book = await Book.insert_one(name='my_test')
        await Author.insert_one(
            name='ali',
            books=[book],
            books2=[book, book],
            book=Book(name='test_book1'),
            book2=None,
            book_detail={'book1': book},
            our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
        )
        _authors = await Author.find(name='ali')
        authors = [i for i in _authors]
        assert len(authors) == 1
        author = authors[0]

        assert isinstance(book, Book)
        assert book.id
        assert book.name == 'my_test'

        assert author.name == 'ali'
        assert isinstance(author.books, list)
        assert len(author.books) == 1
        assert author.books[0] == book
        assert author.books[0]

        assert isinstance(author.books2, list)
        assert len(author.books2) == 2
        assert author.books2[0] == book
        assert author.books2[1] == book

        assert isinstance(author.book, Book)
        assert author.book.id
        assert author.book.name == 'test_book1'

        assert author.book2 is None

        assert isinstance(author.book_detail, dict)
        assert list(author.book_detail.keys()) == ['book1']
        assert author.book_detail['book1'] == book.id  # Known Issue

        assert isinstance(author.our_book_detail, BookDetail)
        assert author.our_book_detail.detail == 'ok'
        assert author.our_book_detail.book == book
        assert isinstance(author.our_book_detail.more_books, list)
        assert len(author.our_book_detail.more_books) == 1
        assert isinstance(author.our_book_detail.more_books[0], list)
        assert len(author.our_book_detail.more_books[0]) == 2
        assert author.our_book_detail.more_books[0][0] == book
        assert author.our_book_detail.more_books[0][1] == book

    async def test_insert_one_invalid_model(self):
        book = await Book.insert_one(name='my_test')
        try:
            await InvalidModel.insert_one(new_book={'book': book})
        except DatabaseError as e:
            assert (
                e.args[0]
                == 'Panther does not support dict[str, tests.test_database_advance.Book] as a field type for unwrapping.'
            )

    # New comprehensive test cases
    async def test_find_one_or_insert_existing(self):
        """Test find_one_or_insert when document exists"""
        book = await Book.insert_one(name='existing_book')

        result, is_inserted = await Book.find_one_or_insert(name='existing_book')

        assert not is_inserted
        assert result == book
        assert result.name == 'existing_book'

    async def test_find_one_or_insert_new(self):
        """Test find_one_or_insert when document doesn't exist"""
        result, is_inserted = await Book.find_one_or_insert(name='new_book')

        assert is_inserted
        assert isinstance(result, Book)
        assert result.name == 'new_book'
        assert result.id

    async def test_find_one_or_raise_found(self):
        """Test find_one_or_raise when document exists"""
        book = await Book.insert_one(name='existing_book')

        result = await Book.find_one_or_raise(name='existing_book')

        assert result == book
        assert result.name == 'existing_book'

    async def test_find_one_or_raise_not_found(self):
        """Test find_one_or_raise when document doesn't exist"""
        try:
            await Book.find_one_or_raise(name='non_existent_book')
            assert False, 'Should have raised NotFoundAPIError'
        except NotFoundAPIError as e:
            assert e.detail == 'Book Does Not Exist'

    async def test_exists_true(self):
        """Test exists when document exists"""
        await Book.insert_one(name='existing_book')

        result = await Book.exists(name='existing_book')

        assert result is True

    async def test_exists_false(self):
        """Test exists when document doesn't exist"""
        result = await Book.exists(name='non_existent_book')

        assert result is False

    async def test_cursor_operations(self):
        """Test cursor operations: skip, limit, sort"""
        # Insert multiple books
        books = []
        for i in range(10):
            book = await Book.insert_one(name=f'book_{i}')
            books.append(book)

        # Test skip and limit
        cursor = await Book.find()
        cursor = cursor.skip(2).limit(3)
        results = [book async for book in cursor]

        assert len(results) == 3
        assert results[0].name == 'book_2'
        assert results[1].name == 'book_3'
        assert results[2].name == 'book_4'

    async def test_cursor_sort(self):
        """Test cursor sorting"""
        # Insert books with different names
        await Book.insert_one(name='zebra')
        await Book.insert_one(name='apple')
        await Book.insert_one(name='banana')

        # Test ascending sort
        cursor = await Book.find()
        cursor = cursor.sort([('name', 1)])
        results = [book async for book in cursor]

        assert len(results) == 3
        assert results[0].name == 'apple'
        assert results[1].name == 'banana'
        assert results[2].name == 'zebra'

        # Test descending sort
        cursor = await Book.find()
        cursor = cursor.sort([('name', -1)])
        results = [book async for book in cursor]

        assert len(results) == 3
        assert results[0].name == 'zebra'
        assert results[1].name == 'banana'
        assert results[2].name == 'apple'

    async def test_update_with_complex_data(self):
        """Test update operations with complex nested data"""
        book = await Book.insert_one(name='original_book')
        author = await Author.insert_one(
            name='original_author',
            books=[book],
            books2=[book],
            book=book,
            book2=None,
            book_detail={'book1': book},
            our_book_detail=BookDetail(detail='original', book=book, more_books=[[book]]),
        )

        # Update with new book
        new_book = await Book.insert_one(name='new_book')

        await Author.update_one(
            {'name': 'original_author'},
            name='updated_author',
            books=[new_book],
            book=new_book,
            our_book_detail=BookDetail(detail='updated', book=new_book, more_books=[[new_book]]),
        )

        updated_author = await Author.find_one(name='updated_author')
        assert updated_author.name == 'updated_author'
        assert len(updated_author.books) == 1
        assert updated_author.books[0] == new_book
        assert updated_author.book == new_book
        assert updated_author.our_book_detail.detail == 'updated'

    async def test_bulk_operations(self):
        """Test bulk insert and update operations"""
        # Bulk insert
        books_data = [{'name': 'bulk_book'} for _ in range(5)]
        books = await Book.insert_many(books_data)

        assert len(books) == 5
        for book in books:
            assert book.name == 'bulk_book'

        # Bulk update
        updated_count = await Book.update_many({'name': 'bulk_book'}, name='updated_bulk_book')

        assert updated_count == 5

        # Verify updates
        updated_books = await Book.find(name='updated_bulk_book')
        count = sum(1 for _ in updated_books)
        assert count == 5

    async def test_empty_collection_operations(self):
        """Test operations on empty collections"""
        # Test find on empty collection
        books = await Book.find()
        count = sum(1 for _ in books)
        assert count == 0

        # Test count on empty collection
        count = await Book.count()
        assert count == 0

        # Test find_one on empty collection
        book = await Book.find_one(name='any_name')
        assert book is None

        # Test first/last on empty collection
        first_book = await Book.first()
        assert first_book is None

        last_book = await Book.last()
        assert last_book is None

    async def test_model_validation_errors(self):
        """Test handling of invalid data"""
        # Test with missing required fields
        try:
            await Book.insert_one()  # Missing name field
            assert False, 'Should have raised validation error'
        except DatabaseError as e:
            assert 'Book(name="Field required")' == str(e)

    async def test_complex_nested_queries(self):
        """Test complex nested queries with multiple conditions"""
        # Create test data
        book1 = await Book.insert_one(name='book1')
        book2 = await Book.insert_one(name='book2')

        author1 = await Author.insert_one(
            name='author1',
            books=[book1],
            books2=[book1],
            book=book1,
            book_detail={'book1': book1},
            our_book_detail=BookDetail(detail='detail1', book=book1, more_books=[[book1]]),
        )

        author2 = await Author.insert_one(
            name='author2',
            books=[book2],
            books2=[book2],
            book=book2,
            book_detail={'book2': book2},
            our_book_detail=BookDetail(detail='detail2', book=book2, more_books=[[book2]]),
        )

        # Complex query
        authors = await Author.find(name='author1')
        results = [author for author in authors]
        assert len(results) == 1
        assert results[0].name == 'author1'

    async def test_save_operations(self):
        """Test save operations for both insert and update"""
        # Test save for new object (insert)
        new_book = Book(name='new_book_save')
        await new_book.save()

        assert new_book.id is not None
        assert new_book.name == 'new_book_save'

        # Verify it was actually saved
        saved_book = await Book.find_one(name='new_book_save')
        assert saved_book is not None
        assert saved_book.id == new_book.id

        # Test save for existing object (update)
        new_book.name = 'updated_book_save'
        await new_book.save()

        # Verify update
        updated_book = await Book.find_one(name='updated_book_save')
        assert updated_book is not None
        assert updated_book.id == new_book.id

    async def test_concurrent_operations(self):
        """Test concurrent operations (basic simulation)"""
        # Insert multiple books concurrently
        import asyncio

        async def insert_book(name):
            return await Book.insert_one(name=name)

        # Create multiple concurrent insertions
        tasks = [insert_book(f'concurrent_book_{i}') for i in range(5)]
        books = await asyncio.gather(*tasks)

        assert len(books) == 5
        for i, book in enumerate(books):
            assert book.name == f'concurrent_book_{i}'
            assert book.id is not None

    async def test_large_dataset_operations(self):
        """Test operations with larger datasets"""
        # Insert larger dataset
        books_data = [{'name': f'large_book_{i}'} for i in range(100)]
        books = await Book.insert_many(books_data)

        assert len(books) == 100

        # Test pagination with large dataset
        cursor = await Book.find()
        cursor = cursor.skip(50).limit(25)
        results = [book async for book in cursor]

        assert len(results) == 25
        assert results[0].name == 'large_book_50'
        assert results[-1].name == 'large_book_74'

        # Test count on large dataset
        count = await Book.count()
        assert count >= 100

    async def test_edge_cases(self):
        """Test various edge cases"""
        # Test with empty string
        book = await Book.insert_one(name='')
        assert book.name == ''

        # Test with very long name
        long_name = 'a' * 1000
        book = await Book.insert_one(name=long_name)
        assert book.name == long_name

        # Test with special characters
        special_name = 'book_with_!@#$%^&*()_+-=[]{}|;:,.<>?'
        book = await Book.insert_one(name=special_name)
        assert book.name == special_name

    async def test_relationship_integrity(self):
        """Test relationship integrity and cascading effects"""
        # Create books and authors with relationships
        book1 = await Book.insert_one(name='book1')
        book2 = await Book.insert_one(name='book2')

        author = await Author.insert_one(
            name='test_author',
            books=[book1, book2],
            books2=[book1, book2],
            book=book1,
            book_detail={'book1': book1, 'book2': book2},
            our_book_detail=BookDetail(detail='test', book=book1, more_books=[[book1, book2]]),
        )

        # Verify relationships are properly established
        assert len(author.books) == 2
        assert len(author.books2) == 2
        assert author.book == book1
        assert len(author.our_book_detail.more_books[0]) == 2

    async def test_error_handling_edge_cases(self):
        """Test error handling for various edge cases"""
        # Test with None values where not allowed
        try:
            await Book.insert_one(name=None)
            assert False, 'Should have raised validation error'
        except Exception:
            pass  # Expected to fail

        # Test with invalid data types
        try:
            await Book.insert_one(name=123)  # Should be string
            assert False, 'Should have raised validation error'
        except Exception:
            pass  # Expected to fail

    async def test_performance_optimizations(self):
        """Test performance-related operations"""
        # Test batch operations
        batch_size = 50
        books_data = [{'name': f'batch_book_{i}'} for i in range(batch_size)]

        start_time = asyncio.get_event_loop().time()
        books = await Book.insert_many(books_data)
        end_time = asyncio.get_event_loop().time()

        assert len(books) == batch_size
        # Basic performance check (should complete in reasonable time)
        assert end_time - start_time < 0.1  # Should complete within 0.1 seconds

    async def test_data_consistency(self):
        """Test data consistency across operations"""
        # Insert book
        book = await Book.insert_one(name='consistency_test')

        # Verify it exists
        found_book = await Book.find_one(name='consistency_test')
        assert found_book == book

        # Update it
        await Book.update_one({'name': 'consistency_test'}, name='updated_consistency_test')

        # Verify update
        updated_book = await Book.find_one(name='updated_consistency_test')
        assert updated_book is not None
        assert updated_book.id == book.id

        # Verify old name doesn't exist
        old_book = await Book.find_one(name='consistency_test')
        assert old_book is None

    async def test_partial_update(self):
        """Test partial update (patch) only updates specified fields"""
        # Insert a book with all fields
        book = await TestBook.insert_one(name='partial_book', author='original_author', pages_count=123)
        # Partial update: only update author
        await TestBook.update_one({'id': book.id}, author='patched_author')
        # Fetch and check
        updated = await TestBook.find_one(id=book.id)
        assert updated.author == 'patched_author'
        assert updated.name == 'partial_book'
        assert updated.pages_count == 123
        # Partial update: only update pages_count
        await TestBook.update_one({'id': book.id}, pages_count=456)
        updated2 = await TestBook.find_one(id=book.id)
        assert updated2.pages_count == 456
        assert updated2.author == 'patched_author'
        assert updated2.name == 'partial_book'

    async def test_first(self):
        """Test getting the first document matching a filter"""
        await TestBook.insert_one(name='first1', author='a', pages_count=1)
        await TestBook.insert_one(name='first2', author='a', pages_count=2)
        first = await TestBook.first(author='a')
        assert first is not None
        assert first.author == 'a'
        assert first.name in ['first1', 'first2']

    async def test_last(self):
        """Test getting the last document matching a filter"""
        await TestBook.insert_one(name='last1', author='b', pages_count=1)
        await TestBook.insert_one(name='last2', author='b', pages_count=2)
        last = await TestBook.last(author='b')
        assert last is not None
        assert last.author == 'b'
        assert last.name in ['last1', 'last2']

    async def test_save_nested_models(self):
        """Test saving a model with nested BaseModel fields"""
        viewer = Viewer(first_name='Ali')
        book = await Book.insert_one(name='nested_book')
        library = await Library.insert_one(name='Central', books=[book], viewer=viewer)
        assert library.id
        assert library.name == 'Central'
        assert isinstance(library.books, list)
        assert library.books[0] == book
        assert isinstance(library.viewer, Viewer)
        assert library.viewer.first_name == 'Ali'


class TestPantherDB(_BaseDatabaseTestCase, IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {'class': 'panther.db.connections.PantherDBConnection', 'path': cls.DB_PATH},
        }
        Panther(__name__, configs=__name__, urls={})

    def tearDown(self) -> None:
        db.session.collection('Book').drop()
        db.session.collection('Author').drop()
        db.session.collection('Publisher').drop()
        db.session.collection('TestBook').drop()
        db.session.collection('Library').drop()

    @classmethod
    def tearDownClass(cls):
        config.refresh()
        Path(cls.DB_PATH).unlink(missing_ok=True)


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
        db.session.drop_collection('Author')
        db.session.drop_collection('Publisher')
        db.session.drop_collection('TestBook')
        db.session.drop_collection('Library')

    @classmethod
    def tearDownClass(cls) -> None:
        config.refresh()

    async def test_insert_one_raw_document(self):
        book = await Book.insert_one(name='my_test')
        author = await Author.insert_one(
            name='ali',
            books=[book.model_dump()],
            books2=[book.id, book],
            book=Book(name='test_book1'),
            book2=None,
            book_detail={'book1': book},
            our_book_detail=BookDetail(detail='ok', book=book, more_books=[[book, book]]),
        )

        document = await db.session['Author'].find_one()
        assert isinstance(document, dict)
        assert list(document.keys()) == [
            '_id',
            'name',
            'books',
            'books2',
            'book',
            'book2',
            'book_detail',
            'our_book_detail',
        ]

        assert document['_id'] == author._id

        assert document['name'] == 'ali'

        assert isinstance(document['books'], list)
        assert len(document['books']) == 1
        assert isinstance(document['books'][0], bson.ObjectId)
        assert document['books'][0] == book._id

        assert isinstance(document['books2'], list)
        assert len(document['books2']) == 2
        assert isinstance(document['books2'][0], bson.ObjectId)
        assert document['books2'][0] == book._id
        assert isinstance(document['books2'][1], bson.ObjectId)
        assert document['books2'][1] == book._id

        assert isinstance(document['book'], bson.ObjectId)
        assert document['book'] != book._id  # A new book

        assert document['book2'] is None

        assert isinstance(document['book_detail'], dict)
        assert list(document['book_detail'].keys()) == ['book1']
        assert isinstance(document['book_detail']['book1'], bson.ObjectId)
        assert document['book_detail']['book1'] == book._id

        assert isinstance(document['our_book_detail'], dict)
        assert list(document['our_book_detail'].keys()) == ['detail', 'book', 'more_books']
        assert document['our_book_detail']['detail'] == 'ok'
        assert isinstance(document['our_book_detail']['book'], bson.ObjectId)
        assert document['our_book_detail']['book'] == book._id
        assert isinstance(document['our_book_detail']['more_books'], list)
        assert len(document['our_book_detail']['more_books']) == 1
        assert isinstance(document['our_book_detail']['more_books'][0], list)
        assert len(document['our_book_detail']['more_books'][0]) == 2
        assert isinstance(document['our_book_detail']['more_books'][0][0], bson.ObjectId)
        assert document['our_book_detail']['more_books'][0][0] == book._id
        assert isinstance(document['our_book_detail']['more_books'][0][1], bson.ObjectId)
        assert document['our_book_detail']['more_books'][0][1] == book._id

    async def test_aggregation_pipeline(self):
        """Test MongoDB aggregation pipeline"""
        # Insert test data
        publishers = [
            {'name': 'Publisher A', 'rating': 4.5, 'is_active': True},
            {'name': 'Publisher B', 'rating': 3.8, 'is_active': True},
            {'name': 'Publisher C', 'rating': 4.2, 'is_active': False},
            {'name': 'Publisher D', 'rating': 4.7, 'is_active': True},
        ]

        await Publisher.insert_many(publishers)

        # Test aggregation pipeline
        pipeline = [{'$match': {'is_active': True}}, {'$group': {'_id': None, 'avg_rating': {'$avg': '$rating'}}}]

        results = await Publisher.aggregate(pipeline)
        results_list = list(results)

        assert len(results_list) == 1
        assert 'avg_rating' in results_list[0]
        # Should be average of 4.5, 3.8, and 4.7 (active publishers only)
        expected_avg = (4.5 + 3.8 + 4.7) / 3
        assert abs(results_list[0]['avg_rating'] - expected_avg) < 0.01

    async def test_mongodb_specific_features(self):
        """Test MongoDB-specific features like ObjectId handling"""
        # Test ObjectId conversion
        book = await Book.insert_one(name='mongodb_test')

        # Verify _id property works correctly
        assert hasattr(book, '_id')
        assert isinstance(book._id, bson.ObjectId)
        assert str(book._id) == str(book.id)

        # Test querying by ObjectId
        found_book = await Book.find_one(id=book._id)
        assert found_book == book

        # Test querying by string ID
        found_book_str = await Book.find_one(id=str(book._id))
        assert found_book_str == book

    async def test_mongodb_complex_queries(self):
        """Test complex MongoDB queries with operators"""
        # Insert test data with various ratings
        publishers = [
            {'name': 'High Rated', 'rating': 4.8, 'is_active': True},
            {'name': 'Medium Rated', 'rating': 3.5, 'is_active': True},
            {'name': 'Low Rated', 'rating': 2.1, 'is_active': False},
            {'name': 'Top Rated', 'rating': 4.9, 'is_active': True},
            {'name': 'Top Rated', 'rating': 5.9, 'is_active': False},
        ]

        await Publisher.insert_many(publishers)

        # Test complex query with multiple conditions
        high_rated_active = await Publisher.find({'rating': {'$gte': 4.0}, 'is_active': True})
        results = [pub for pub in high_rated_active]

        assert len(results) == 2  # High Rated, Top Rated, and one more
        for pub in results:
            assert pub.rating >= 4.0
            assert pub.is_active is True

    async def test_mongodb_bulk_operations(self):
        """Test MongoDB-specific bulk operations"""
        # Test bulk write operations
        books_data = [{'name': f'mongodb_bulk_{i}'} for i in range(10)]
        books = await Book.insert_many(books_data)

        # Test bulk update with MongoDB operators
        update_result = await Book.update_many(
            {'name': {'$regex': 'mongodb_bulk_'}}, {'$set': {'name': 'updated_mongodb_bulk'}}
        )

        # Verify all documents were updated
        updated_books = await Book.find(name='updated_mongodb_bulk')
        count = sum(1 for _ in updated_books)
        assert count == 10

    async def test_mongodb_data_types(self):
        """Test MongoDB-specific data types and handling"""
        # Test with various data types that MongoDB handles well
        test_data = {
            'name': 'data_type_test',
            'rating': 4.5,
            'is_active': True,
            'tags': ['fiction', 'adventure'],
            'metadata': {'pages': 300, 'language': 'English'},
        }

        # Create a test model for this
        class TestModel(Model):
            name: str
            rating: float
            is_active: bool
            tags: list[str]
            metadata: dict

        publisher = await TestModel.insert_one(**test_data)

        assert publisher.name == 'data_type_test'
        assert publisher.rating == 4.5
        assert publisher.is_active is True
        assert publisher.tags == ['fiction', 'adventure']
        assert publisher.metadata == {'pages': 300, 'language': 'English'}

    async def test_mongodb_error_handling(self):
        """Test MongoDB-specific error handling"""
        # Test with invalid ObjectId
        try:
            await Book.find_one(id='invalid_object_id')
            # Should handle gracefully
        except Exception as e:
            # Should not crash the application
            assert 'invalid' in str(e).lower() or 'objectid' in str(e).lower()
