import asyncio
import contextlib
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from pantherdb import PantherDB

from panther.cli.utils import import_error
from panther.configs import config
from panther.utils import Singleton

try:
    from redis.asyncio import Redis as _Redis
except ImportError:
    # This '_Redis' is not going to be used,
    #   If user really wants to use redis,
    #   we are going to force him to install it in `panther._load_configs.load_redis`
    _Redis = type('_Redis', (), {'__new__': lambda x: x})

if TYPE_CHECKING:
    from pymongo.database import Database


class BaseDatabaseConnection:
    def __init__(self, *args, **kwargs):
        """Initialized in application startup"""
        self.init(*args, **kwargs)

    @abstractmethod
    def init(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def session(self):
        pass


class MongoDBConnection(BaseDatabaseConnection):
    def init(
            self,
            host: str = 'localhost',
            port: int = 27017,
            document_class: dict[str, Any] | None = None,
            tz_aware: bool | None = None,
            connect: bool | None = None,
            type_registry=None,  # type: bson.codec_options.TypeRegistry
            database: str | None = None,
            **kwargs: Any,
    ) -> None:
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ModuleNotFoundError as e:
            raise import_error(e, package='motor')

        with contextlib.suppress(ImportError):
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        self._client: AsyncIOMotorClient = AsyncIOMotorClient(
            host=host,
            port=port,
            document_class=document_class,
            tz_aware=tz_aware,
            connect=connect,
            type_registry=type_registry,
            **kwargs,
        )
        self._database: Database = self._client.get_database(name=database)

    @property
    def session(self):
        return self._database


class PantherDBConnection(BaseDatabaseConnection):
    def init(self, path: str | None = None, encryption: bool = False):
        params = {'db_name': path, 'return_dict': True, 'return_cursor': True}
        if encryption:
            try:
                import cryptography
            except ImportError as e:
                raise import_error(e, package='cryptography')
            params['secret_key'] = config.SECRET_KEY

        self._connection: PantherDB = PantherDB(**params)

    @property
    def session(self):
        return self._connection


class DatabaseConnection(Singleton):
    @property
    def session(self):
        return config.DATABASE.session


class RedisConnection(Singleton, _Redis):
    is_connected: bool = False

    def __init__(
            self,
            init: bool = False,
            host: str = 'localhost',
            port: int = 6379,
            db: int = 0,
            websocket_db: int = 0,
            **kwargs
    ):
        if init:
            self.host = host
            self.port = port
            self.db = db
            self.websocket_db = websocket_db
            self.kwargs = kwargs

            super().__init__(host=host, port=port, db=db, **kwargs)
            self.is_connected = True
            self.sync_ping()

    def sync_ping(self):
        from redis import Redis

        Redis(host=self.host, port=self.port, socket_timeout=3, **self.kwargs).ping()

    async def execute_command(self, *args, **options):
        if self.is_connected:
            return await super().execute_command(*args, **options)
        msg = '`REDIS` is not found in `configs`'
        raise ValueError(msg)

    def create_connection_for_websocket(self) -> _Redis:
        if not hasattr(self, 'websocket_connection'):
            self.websocket_connection = _Redis(
                host=self.host,
                port=self.port,
                db=self.websocket_db,
                **self.kwargs
            )
        return self.websocket_connection


db: DatabaseConnection = DatabaseConnection()
redis: RedisConnection = RedisConnection()
