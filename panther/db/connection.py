from typing import TYPE_CHECKING

from pantherdb import PantherDB
from redis import Redis

from panther.configs import config
from panther.utils import Singleton

if TYPE_CHECKING:
    from pymongo.database import Database


class DBSession(Singleton):
    _db_name: str

    def __init__(self, db_url: str | None = None):
        if db_url:
            if (seperator := db_url.find(':')) == -1:
                # ex: db_url = 'some_db' (or something without ':')
                seperator = None
            self._db_name = db_url[:seperator]
            match self._db_name:
                case 'mongodb':
                    self._create_mongodb_session(db_url)
                case 'pantherdb':
                    self._create_pantherdb_session(db_url[12:])
                case _:
                    msg = f'We are not support "{self._db_name}" database yet'
                    raise ValueError(msg)

    @property
    def session(self):
        return self._session

    @property
    def name(self) -> str:
        return self._db_name

    def _create_mongodb_session(self, db_url: str) -> None:
        from pymongo import MongoClient

        self._client: MongoClient = MongoClient(db_url)
        self._session: Database = self._client.get_database()

    def _create_pantherdb_session(self, db_url: str) -> None:
        self._session: PantherDB = PantherDB(db_url, return_dict=True, secret_key=config['secret_key'])

    def close(self) -> None:
        if self._db_name == 'mongodb':
            self._client.close()
        else:
            self._session.close()


class RedisConnection(Singleton, Redis):
    """Redis connection here works for per request things (caching, ...)"""

    is_connected: bool = False

    def __init__(self, host: str | None = None, port: int | None = None, **kwargs):
        if host and port:
            super().__init__(host=host, port=port, **kwargs)
            self.is_connected = True

    def execute_command(self, *args, **options) -> any:
        if not hasattr(self, 'connection_pool'):
            msg = "'RedisConnection' object has no attribute 'connection_pool'. Hint: Check your redis middleware"
            raise AttributeError(msg)
        return super().execute_command(*args, **options)


db: DBSession = DBSession()
redis: Redis = RedisConnection()
