from panther.logger import logger
from panther.request import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from panther.middlewares.base import BaseMiddleware


class Singleton(object):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]


class DBSession(Singleton):
    _session: Session

    def __init__(self, db_url: str | None = None):
        logger.info(f'{db_url = }')
        if db_url:
            self.db_url = db_url
            # engine = create_async_engine(db_url)
            engine = create_engine(db_url, echo=True)
            Base = declarative_base()  # TODO: Testing ...
            Base.metadata.create_all(engine)  # TODO: Testing ...

            # logger.info('create_session')
            # if database_type == 'SQLite':
            #     _create_engine = create_async_engine
            #     connect_args = {'check_same_thread': False}
            # else:
            #     _create_engine = create_engine
            #     connect_args = {}
            # engine = _create_engine(database_url, connect_args)
            # cls._instances = sessionmaker(autocommit=False, autoflush=False, bind=engine)

            _Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self._session = _Session()

    @property
    def session(self) -> Session:
        logger.info(f'{self.db_url = }')
        return self._session

class Middleware(BaseMiddleware):

    async def before(self, request: Request):
        self.db = DBSession(db_url=request.db_url)
        logger.info(f'{self.db = }')
        logger.info(f'{self.db.session = }')
        return request

    # async def after(self, response: Response):
    #     self.db.session.close()
    #     logger.info(f'{self.db = }')
    #     return response


db: DBSession = DBSession()
