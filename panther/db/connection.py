from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


class DBSession(Singleton):
    _session: Session

    def __init__(self, db_url: str | None = None):
        if db_url:
            self.db_url = db_url
            engine = create_engine(db_url)
            _Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self._session = _Session()

    @property
    def session(self) -> Session:
        return self._session

class RedisConnection(Singleton, Redis):
    def __init__(self, host: str | None = None, port: int | None = None, **kwargs):
        if host and port:
            super().__init__(host=host, port=port, **kwargs)


db: DBSession = DBSession()
redis: Redis = RedisConnection()


