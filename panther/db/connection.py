from redis import Redis
from pantherdb import PantherDB
from panther.configs import config
from panther.cli.utils import import_error_message


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


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
                    raise ValueError(f'We are not support "{self._db_name}" database yet')

    @property
    def session(self):
        return self._session

    @property
    def name(self) -> str:
        return self._db_name

    def _create_mongodb_session(self, db_url: str) -> None:
        try:
            from pymongo import MongoClient
            from pymongo.database import Database
        except ImportError:
            raise ImportError(import_error_message('pymongo'))

        self._client: MongoClient = MongoClient(db_url)
        self._session: Database = self._client.get_database()

    def _create_pantherdb_session(self, db_url: str):
        self._session: PantherDB = PantherDB(db_url, return_dict=True, secret_key=config['secret_key'])

    def close(self):
        if self._db_name == 'mongodb':
            self._client.close()
        else:
            self._session.close()


class RedisConnection(Singleton, Redis):
    is_connected: bool = False

    def __init__(self, host: str | None = None, port: int | None = None, **kwargs):
        if host and port:
            super().__init__(host=host, port=port, **kwargs)
            self.is_connected = True


db: DBSession = DBSession()
redis: Redis = RedisConnection()
