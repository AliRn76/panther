from redis import Redis
from typing import Union
from pymongo import MongoClient
from pymongo.database import Database
from sqlalchemy.orm import Session, sessionmaker


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


class DBSession(Singleton):
    _session: Union[Session, Database]
    _client: MongoClient
    _name: str

    def __init__(self, db_url: str | None = None):
        if db_url:
            self._name = db_url[:db_url.find(':')]
            match self._name:
                case 'mongodb':
                    self._create_mongo_session(db_url)
                case 'sqlite':
                    self._create_sqlite_session(db_url)
                case _:
                    raise ValueError(f'We are support {self._name} Database yet')

    @property
    def session(self) -> Union[Session, Database]:
        return self._session

    @property
    def name(self) -> str:
        return self._name

    def _create_mongo_session(self, db_url: str) -> None:
        self._client = MongoClient(db_url)
        self._session: Database = self._client.get_database()

    def _create_sqlite_session(self, db_url: str):
        from sqlalchemy import create_engine
        engine = create_engine(db_url)
        _Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self._session: Session = _Session()

    def close(self):
        if self._name == 'mongodb':
            self._client.close()
        else:
            self._session.close()


class RedisConnection(Singleton, Redis):
    def __init__(self, host: str | None = None, port: int | None = None, **kwargs):
        if host and port:
            super().__init__(host=host, port=port, **kwargs)


db: DBSession = DBSession()
redis: Redis = RedisConnection()


