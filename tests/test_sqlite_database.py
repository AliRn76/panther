from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase

import pytest
from pydantic import BaseModel, Field

from panther import Panther
from panther.configs import config
from panther.db import Model
from panther.db.connections import SQLiteConnection, db
from panther.db.queries.sqlite_queries import BaseSQLiteQuery, SQLiteCursor
from panther.exceptions import DatabaseError
from panther.utils import run_coroutine

aiosqlite = pytest.importorskip('aiosqlite')


class SQLiteAuthor(Model):
    name: str


class SQLiteMetadata(BaseModel):
    edition: str


class SQLiteBook(Model):
    title: str
    pages: int
    published: bool = False
    tags: list[str] = Field(default_factory=list)
    metadata: SQLiteMetadata | None = None
    author: SQLiteAuthor | None = None


class TestSQLiteConfig(TestCase):
    DB_PATH = Path('test_sqlite_config.sqlite3')

    def tearDown(self):
        config.refresh()
        self.DB_PATH.unlink(missing_ok=True)

    def test_sqlite_engine_sets_query_engine(self):
        global DATABASE
        DATABASE = {'engine': {'class': 'panther.db.connections.SQLiteConnection', 'path': self.DB_PATH}}

        Panther(__name__, configs=__name__, urls={})

        assert isinstance(config.DATABASE, SQLiteConnection)
        assert config.QUERY_ENGINE is BaseSQLiteQuery


class TestSQLiteDatabase(IsolatedAsyncioTestCase):
    DB_PATH = Path('test_sqlite.sqlite3')

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {'engine': {'class': 'panther.db.connections.SQLiteConnection', 'path': cls.DB_PATH}}
        Panther(__name__, configs=__name__, urls={})
        run_coroutine(db.session.create_tables(SQLiteAuthor, SQLiteBook))

    async def asyncTearDown(self):
        await db.session.execute('DELETE FROM "SQLiteBook"')
        await db.session.execute('DELETE FROM "SQLiteAuthor"')

    @classmethod
    def tearDownClass(cls):
        run_coroutine(db.session.close())
        config.refresh()
        cls.DB_PATH.unlink(missing_ok=True)

    async def test_insert_find_update_delete(self):
        book = await SQLiteBook.insert_one(
            title='Panther SQL',
            pages=120,
            published=True,
            tags=['sql', 'sqlite'],
            metadata=SQLiteMetadata(edition='first'),
        )

        found = await SQLiteBook.find_one(title='Panther SQL')
        assert found == book
        assert found.published is True
        assert found.tags == ['sql', 'sqlite']
        assert found.metadata.edition == 'first'

        assert await SQLiteBook.update_one({'id': book.id}, pages=121)
        await found.reload()
        assert found.pages == 121

        assert await SQLiteBook.delete_one(id=book.id)
        assert await SQLiteBook.find_one(id=book.id) is None

    async def test_find_cursor_skip_limit_sort(self):
        await SQLiteBook.insert_many(
            [
                {'title': 'c', 'pages': 3},
                {'title': 'a', 'pages': 1},
                {'title': 'b', 'pages': 2},
            ],
        )

        cursor = await SQLiteBook.find()
        assert isinstance(cursor, SQLiteCursor)

        results = [book async for book in cursor.sort([('title', 1)]).skip(1).limit(1)]
        assert [book.title for book in results] == ['b']
        assert len(list(await SQLiteBook.all())) == 3

    async def test_model_field_is_stored_as_foreign_key_and_hydrated(self):
        author = await SQLiteAuthor.insert_one(name='Ada')
        book = await SQLiteBook.insert_one(title='Relational Panther', pages=10, author=author)

        found = await SQLiteBook.find_one(id=book.id)

        assert found.author == author

    async def test_find_one_or_insert_and_count(self):
        first, was_inserted = await SQLiteBook.find_one_or_insert(title='Unique-ish', pages=1)
        second, was_inserted_again = await SQLiteBook.find_one_or_insert(title='Unique-ish', pages=1)

        assert was_inserted is True
        assert was_inserted_again is False
        assert first.id == second.id
        assert await SQLiteBook.count(title='Unique-ish') == 1

    async def test_unsupported_sqlite_operations_raise_database_error(self):
        with pytest.raises(DatabaseError):
            await SQLiteBook.aggregate([])

        with pytest.raises(DatabaseError):
            await SQLiteBook.update_many({'title': 'x'}, {'$set': {'title': 'y'}})
