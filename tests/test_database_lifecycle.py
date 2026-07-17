from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.configs import config
from panther.db.connections import BaseDatabaseConnection, db


class LifecycleDatabaseConnection(BaseDatabaseConnection):
    def init(self):
        self.events = []

    @property
    def session(self):
        return None

    async def startup(self) -> None:
        self.events.append('startup')

    async def shutdown(self) -> None:
        self.events.append('shutdown')


class TestDatabaseLifecycle(IsolatedAsyncioTestCase):
    async def test_database_connection_delegates_lifecycle_hooks(self):
        previous_database = config.DATABASE
        database = LifecycleDatabaseConnection()
        config.DATABASE = database
        try:
            await db.startup()
            await db.shutdown()
        finally:
            config.DATABASE = previous_database

        assert database.events == ['startup', 'shutdown']

    async def test_database_connection_yields_the_backend_session(self):
        previous_database = config.DATABASE
        database = LifecycleDatabaseConnection()
        config.DATABASE = database
        try:
            async with db.session_context() as session:
                assert session is database.session
        finally:
            config.DATABASE = previous_database

    async def test_application_lifespan_runs_database_lifecycle_hooks(self):
        previous_database = config.DATABASE
        previous_has_websocket = config.HAS_WS
        database = LifecycleDatabaseConnection()
        application = object.__new__(Panther)

        async def send(_message):
            pass

        try:
            config.DATABASE = database
            config.HAS_WS = False

            async def startup_message():
                return {'type': 'lifespan.startup'}

            await application(scope={'type': 'lifespan'}, receive=startup_message, send=send)

            async def shutdown_message():
                return {'type': 'lifespan.shutdown'}

            await application(scope={'type': 'lifespan'}, receive=shutdown_message, send=send)
        finally:
            config.DATABASE = previous_database
            config.HAS_WS = previous_has_websocket

        assert database.events == ['startup', 'shutdown']
