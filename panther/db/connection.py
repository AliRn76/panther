from redis import Redis
from typing import Union
from tinydb import TinyDB
from pymongo import MongoClient
from pymongo.database import Database


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


class DBSession(Singleton):
    _session: Union[TinyDB, Database]
    _client: MongoClient
    _name: str

    def __init__(self, db_url: str | None = None):
        if db_url:
            self._name = db_url[:db_url.find(':')]
            match self._name:
                case 'mongodb':
                    # TODO: Check pymongo installed or not
                    self._create_mongodb_session(db_url)
                case 'tinydb':
                    self._create_tinydb_session(db_url[9:])
                case _:
                    # TODO: self._name does not have a last character if only path passed
                    raise ValueError(f'We are support {self._name} Database yet')

    @property
    def session(self) -> Union[TinyDB, Database]:
        return self._session

    @property
    def name(self) -> str:
        return self._name

    def _create_mongodb_session(self, db_url: str) -> None:
        self._client = MongoClient(db_url)
        self._session: Database = self._client.get_database()

    def _create_tinydb_session(self, db_url: str):
        self._session: TinyDB = TinyDB(db_url)

    def close(self):
        if self._name == 'mongodb':
            self._client.close()
        else:
            self._session.close()


class RedisConnection(Singleton, Redis):
    is_connected: bool = False

    def __init__(self, host: str | None = None, port: int | None = None, **kwargs):
        # TODO: Check redis installed or not
        if host and port:
            super().__init__(host=host, port=port, **kwargs)
            self.is_connected = True


db: DBSession = DBSession()
redis: Redis = RedisConnection()


