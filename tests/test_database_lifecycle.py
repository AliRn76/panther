from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.configs import config
from panther.db.connections import BaseDatabaseConnection, db
from panther.events import Event


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
    def setUp(self):
        Event.clear()

    def tearDown(self):
        Event.clear()

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

        messages = iter(
            [
                {'type': 'lifespan.startup'},
                {'type': 'lifespan.shutdown'},
            ],
        )
        sent_messages = []

        async def receive():
            return next(messages)

        async def send(message):
            sent_messages.append(message)

        try:
            config.DATABASE = database
            config.HAS_WS = False

            await application(scope={'type': 'lifespan'}, receive=receive, send=send)
        finally:
            config.DATABASE = previous_database
            config.HAS_WS = previous_has_websocket

        assert database.events == ['startup', 'shutdown']
        assert sent_messages == [
            {'type': 'lifespan.startup.complete'},
            {'type': 'lifespan.shutdown.complete'},
        ]

    async def test_application_lifespan_awaits_async_shutdown_events(self):
        previous_database = config.DATABASE
        previous_has_websocket = config.HAS_WS
        database = LifecycleDatabaseConnection()
        application = object.__new__(Panther)
        messages = iter(
            [
                {'type': 'lifespan.startup'},
                {'type': 'lifespan.shutdown'},
            ],
        )
        events = []

        @Event.shutdown
        async def shutdown_event():
            events.append('shutdown')

        async def receive():
            return next(messages)

        async def send(_message):
            pass

        try:
            config.DATABASE = database
            config.HAS_WS = False
            await application(scope={'type': 'lifespan'}, receive=receive, send=send)
        finally:
            config.DATABASE = previous_database
            config.HAS_WS = previous_has_websocket

        assert events == ['shutdown']
