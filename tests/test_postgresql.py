"""PostgreSQL integration tests.

Start the local test database with:

    docker run --rm -p 5432:5432 -d --name postgres \
      -e POSTGRES_DB=panther_test -e POSTGRES_USER=postgres \
      -e POSTGRES_PASSWORD=postgres postgres:16
"""

import asyncio
import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

import pytest

POSTGRES_TEST_URL = os.getenv(
    'PANTHER_POSTGRES_TEST_URL',
    'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/panther_test',
)

from sqlalchemy import text

from panther.db.connections import PostgreSQLConnection

pytestmark = pytest.mark.postgresql


class TestPostgreSQLConnection(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connection = None
        self.connection = PostgreSQLConnection(url=POSTGRES_TEST_URL)
        await self.connection.startup()
        async with self.connection.session_context() as session:
            await session.execute(
                text(
                    'CREATE TABLE IF NOT EXISTS panther_postgresql_test_records '
                    '(id INTEGER PRIMARY KEY, value TEXT NOT NULL)',
                ),
            )
            await session.execute(text('TRUNCATE panther_postgresql_test_records'))
            await session.commit()

    async def asyncTearDown(self):
        if self.connection is not None:
            await self.connection.shutdown()

    async def test_startup_and_session_execution(self):
        async with self.connection.session_context() as session:
            result = await session.execute(text('SELECT 1'))

        assert result.scalar_one() == 1

    async def test_session_context_requires_explicit_commit(self):
        async with self.connection.session_context() as session:
            await session.execute(text("INSERT INTO panther_postgresql_test_records VALUES (1, 'saved')"))
            await session.commit()

        async with self.connection.session_context() as session:
            result = await session.execute(text('SELECT value FROM panther_postgresql_test_records WHERE id = 1'))

        assert result.scalar_one() == 'saved'

    async def test_session_context_rolls_back_on_error(self):
        with self.assertRaisesRegex(RuntimeError, 'rollback'):
            async with self.connection.session_context() as session:
                await session.execute(text("INSERT INTO panther_postgresql_test_records VALUES (1, 'rolled back')"))
                raise RuntimeError('rollback')

        async with self.connection.session_context() as session:
            result = await session.execute(text('SELECT COUNT(*) FROM panther_postgresql_test_records'))

        assert result.scalar_one() == 0

    async def test_startup_fails_for_an_unreachable_database(self):
        connection = PostgreSQLConnection(
            url='postgresql+asyncpg://postgres:postgres@127.0.0.1:1/panther_test',
            connect_args={'timeout': 1},
        )
        with self.assertRaises(Exception):
            await asyncio.wait_for(connection.startup(), timeout=2)
        await connection.shutdown()

    async def test_shutdown_disposes_the_engine(self):
        connection = object.__new__(PostgreSQLConnection)
        engine = type('Engine', (), {})()
        engine.dispose = AsyncMock()
        connection._engine = engine

        await connection.shutdown()

        engine.dispose.assert_awaited_once()
