import asyncio
import contextlib
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, get_args, get_origin

import ulid
from pantherdb import PantherDB
from pydantic import BaseModel

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

    @property
    def client(self):
        return self._client


class PantherDBConnection(BaseDatabaseConnection):
    def init(self, path: str | None = None, encryption: bool = False):
        params = {'db_name': path, 'return_dict': True, 'return_cursor': True}
        if encryption:
            try:
                import cryptography  # noqa: F401
            except ImportError as e:
                raise import_error(e, package='cryptography')
            params['secret_key'] = config.SECRET_KEY.encode()

        self._connection: PantherDB = PantherDB(**params)

    @property
    def session(self):
        return self._connection

    @property
    def client(self):
        return self._connection


class SQLiteConnection(BaseDatabaseConnection):
    def init(self, path: str | Path = 'database.sqlite3') -> None:
        try:
            import aiosqlite
        except ModuleNotFoundError as e:
            raise import_error(e, package='aiosqlite')

        self._aiosqlite = aiosqlite
        self.path = Path(path)
        self._connection = None

    @property
    def session(self):
        return self

    @property
    def client(self):
        return self

    async def connection(self):
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = await self._aiosqlite.connect(self.path)
            self._connection.row_factory = self._aiosqlite.Row
            await self._connection.execute('PRAGMA foreign_keys = ON')
            await self._connection.commit()
        return self._connection

    async def execute(self, query: str, params: tuple = ()):
        connection = await self.connection()
        cursor = await connection.execute(query, params)
        await connection.commit()
        return cursor

    async def fetchone(self, query: str, params: tuple = ()):
        cursor = await self.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple = ()):
        cursor = await self.execute(query, params)
        return await cursor.fetchall()

    async def close(self):
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def create_tables(self, *models: type[BaseModel]) -> None:
        if not models:
            models = tuple(config.MODELS)

        for model in models:
            if not hasattr(model, 'model_fields'):
                continue

            columns = ['"id" TEXT PRIMARY KEY']
            foreign_keys = []
            for field_name, field in model.model_fields.items():
                if field_name == 'id':
                    continue

                field_type = self._unwrap_annotation(field.annotation)
                column_name = field_name
                if self._is_model(field_type):
                    column_name = f'{field_name}_id'
                    related_table = self.table_name(field_type)
                    foreign_keys.append(
                        f'FOREIGN KEY ("{column_name}") REFERENCES "{related_table}"("id")',
                    )

                columns.append(f'"{column_name}" {self._column_type(field_type)}')

            columns.extend(foreign_keys)
            query = f'CREATE TABLE IF NOT EXISTS "{self.table_name(model)}" ({", ".join(columns)})'
            await self.execute(query)

    @staticmethod
    def table_name(model: type[BaseModel]) -> str:
        return getattr(model, '__tablename__', None) or model.__name__

    @staticmethod
    def generate_id() -> str:
        return ulid.new()

    @classmethod
    def _unwrap_annotation(cls, annotation):
        origin = get_origin(annotation)
        if origin in (list, dict):
            return annotation
        if origin:
            for arg in get_args(annotation):
                if arg is not type(None):
                    return arg
        return annotation

    @classmethod
    def _is_model(cls, field_type) -> bool:
        from panther.db import Model

        return isinstance(field_type, type) and issubclass(field_type, Model)

    @classmethod
    def _column_type(cls, field_type) -> str:
        if cls._is_model(field_type):
            return 'TEXT'
        if field_type in (str, datetime):
            return 'TEXT'
        if field_type in (int, bool):
            return 'INTEGER'
        if field_type is float:
            return 'REAL'
        return 'TEXT'


class DatabaseConnection(Singleton):
    @property
    def session(self):
        return config.DATABASE.session

    @property
    def is_defined(self):
        return bool(config.DATABASE)

    @property
    def client(self):
        return config.DATABASE.client


class RedisConnection(Singleton, _Redis):
    is_connected: bool = False

    def __init__(
        self,
        init: bool = False,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        **kwargs,
    ):
        if init:
            self.host = host
            self.port = port
            self.db = db
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
            self.websocket_connection = _Redis(host=self.host, port=self.port, db=0, **self.kwargs)
        return self.websocket_connection


db: DatabaseConnection = DatabaseConnection()
redis: RedisConnection = RedisConnection()
