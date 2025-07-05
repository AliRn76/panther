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
from panther.exceptions import DatabaseError

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
