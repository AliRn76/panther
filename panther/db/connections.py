from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from pantherdb import PantherDB

from panther.cli.utils import import_error
from panther.configs import config
from panther.utils import Singleton

try:
    from redis import Redis as _Redis
except ModuleNotFoundError:
    # This '_Redis' is not going to be used,
    #   If user really wants to use redis,
    #   we are going to force him to install it in `panther._load_configs.load_redis`
    _Redis = type('_Redis', (), {'__new__': lambda x: x, 'ping': lambda self: True})

if TYPE_CHECKING:
    from pymongo.database import Database


class DatabaseConnection:
    @abstractmethod
    def create_session(self):
        pass

    @abstractmethod
    def close_session(self):
        pass

    @property
    @abstractmethod
    def session(self):
        pass


class MongoDBConnection(DatabaseConnection):
    def __init__(
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
            from pymongo import MongoClient
        except ModuleNotFoundError as e:
            raise import_error(e, package='pymongo')

        self.host = host
        self.port = port
        self.document_class = document_class
        self.tz_aware = tz_aware
        self.connect = connect
        self.type_registry = type_registry
        self.database = database
        self.kwargs = kwargs

    def create_session(self):
        from pymongo import MongoClient

        self._client: MongoClient = MongoClient(
            host=self.host,
            port=self.port,
            document_class=self.document_class,
            tz_aware=self.tz_aware,
            connect=self.connect,
            type_registry=self.type_registry,
            **self.kwargs,
        )
        self._database: Database = self._client.get_database(name=self.database)

    @property
    def session(self):
        return self._database

    def close_session(self):
        self._client.close()


class PantherDBConnection(DatabaseConnection):
    def __init__(self, path: str | None = None, encryption: bool = False):
        self.path = path
        self.encryption = encryption
        self.params = {'db_name': self.path, 'return_dict': True}
        if self.encryption:
            try:
                import cryptography
            except ModuleNotFoundError as e:
                raise import_error(e, package='cryptography')
            self.params['secret_key'] = config['secret_key']

    def create_session(self):
        self._connection: PantherDB = PantherDB(**self.params)

    @property
    def session(self):
        return self._connection

    def close_session(self):
        pass


class DatabaseSession(Singleton):
    def __init__(self, init: bool = False):
        if init:
            config.database.create_session()

    def close(self):
        config.database.close_session()

    @property
    def session(self):
        return config.database.session


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
            self.ping()

    def create_connection_for_websocket(self) -> _Redis:
        if not hasattr(self, 'websocket_connection'):
            self.websocket_connection = _Redis(
                host=self.host,
                port=self.port,
                db=self.websocket_db,
                **self.kwargs
            )
        return self.websocket_connection


db: DatabaseSession = DatabaseSession()
redis: RedisConnection = RedisConnection()
