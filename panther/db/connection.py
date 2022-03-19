# # from contextvars import ContextVar
# #
# # from panther.logger import logger
# # from sqlalchemy import create_engine
# # from sqlalchemy.orm import Session, sessionmaker
# # from sqlalchemy.ext.asyncio import create_async_engine
# #
# # from panther.exceptions import SessionNotInitialisedError, MissingSessionError
# #
# # # _Session: sessionmaker | None = None
# # _session: ContextVar[Session | None] = ContextVar('session', default=None)
# # __session: sessionmaker | None = None
# #
# # # class DBSession:
# # #     _instances = {}
# # #
# # #     def __new__(cls, *args, **kwargs):
# # #         if cls._instances is None:
# # #             database_url = kwargs.get('database_url')
# # #             database_type = kwargs.get('database_type')
# # #             logger.info('create_session')
# # #             if database_type == 'SQLite':
# # #                 _create_engine = create_async_engine
# # #                 connect_args = {'check_same_thread': False}
# # #             else:
# # #                 _create_engine = create_engine
# # #                 connect_args = {}
# # #             engine = _create_engine(database_url, connect_args)
# # #             cls._instances = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# # #         return cls._instances
# #
# #
# # # db = None
# # def create_session(database_url: str, database_type: str):
# #     global __session
# #
# #     logger.info('create_session')
# #     if database_type == 'SQLite':
# #         engine = create_async_engine(database_url)
# #     else:
# #         engine = create_engine(database_url)
# #     __session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# #     _session.set(__session())
# #
# #
# # # class DBSessionMeta(type):
# # #     # using this metaclass means that we can access db.session as a property at a class level,
# # #     # rather than db().session
# # #     @property
# # #     def session(self) -> Session:
# # #         """Return an instance of Session local to the current async context."""
# # #         if session is None:
# # #             raise SessionNotInitialisedError
# # #
# # #         # session = _session.get()
# # #         # if session is None:
# # #         #     raise MissingSessionError
# # #
# # #         return session
# #
# # #
# # class DBSession:
# #     def __init__(self, commit_on_exit: bool = False):
# #         self.token = None
# #         self.session_args = {}
# #         self.commit_on_exit = commit_on_exit
# #
# #     @property
# #     def session(self) -> Session:
# #         session = _session.get()
# #         if session is None:
# #             logger.critical('DBSession session is None')
# #             raise MissingSessionError
# #         print(f'{session = }')
# #         print(f'{type(session) = }')
# #         return session
# #
# #     def __enter__(self):
# #         global __session
# #
# #         logger.critical('DBSession __enter__')
# #         if not isinstance(__session, sessionmaker):
# #             logger.critical('DBSession __enter__ inside if')
# #             raise SessionNotInitialisedError
# #         self.token = _session.set(__session(**self.session_args))
# #         return type(self)
# #
# #     def __exit__(self, exc_type, exc_value, traceback):
# #         logger.critical('DBSession __exit__')
# #         sess = _session.get()
# #         if exc_type is not None:
# #             sess.rollback()
# #
# #         if self.commit_on_exit:
# #             sess.commit()
# #
# #         sess.close()
# #         _session.reset(self.token)
# #
# #
# # db = DBSession
#
#
# from contextvars import ContextVar
# from typing import Dict, Optional, Union
#
# from sqlalchemy import create_engine
# from sqlalchemy.engine import Engine
# from sqlalchemy.engine.url import URL
# from sqlalchemy.orm import Session, sessionmaker
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from starlette.requests import Request
# from starlette.types import ASGIApp
#
# from fastapi_sqlalchemy.exceptions import MissingSessionError, SessionNotInitialisedError
#
# _Session: sessionmaker | None = None
# _session: ContextVar[Session | None] = ContextVar("_session", default=None)
#
#
# # Create Engine
# # Create SessionMaker
# # with db():
# # set SessionMaker in __enter__
# # reset on __exit__
# class DBSessionMiddleware:
#     def __init__(
#         self,
#         db_url: Optional[Union[str, URL]] = None,
#         custom_engine: Optional[Engine] = None,
#         engine_args: Dict = None,
#         session_args: Dict = None,
#         commit_on_exit: bool = False,
#     ):
#         global _Session
#         engine_args = engine_args or {}
#         self.commit_on_exit = commit_on_exit
#
#         session_args = session_args or {}
#         if not custom_engine and not db_url:
#             raise ValueError("You need to pass a db_url or a custom_engine parameter.")
#         if not custom_engine:
#             engine = create_engine(db_url, **engine_args)
#         else:
#             engine = custom_engine
#         _Session = sessionmaker(bind=engine, **session_args)
#
#     async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
#         with db(commit_on_exit=self.commit_on_exit):
#             response = await call_next(request)
#         return response
#
#
# class DBSessionMeta(type):
#     # using this metaclass means that we can access db.session as a property at a class level,
#     # rather than db().session
#     @property
#     def session(self) -> Session:
#         """Return an instance of Session local to the current async context."""
#         if _Session is None:
#             raise SessionNotInitialisedError
#
#         session = _session.get()
#         if session is None:
#             raise MissingSessionError
#
#         return session
#
#
# class DBSession(metaclass=DBSessionMeta):
#     def __init__(self, session_args: Dict = None, commit_on_exit: bool = False):
#         self.token = None
#         self.session_args = session_args or {}
#         self.commit_on_exit = commit_on_exit
#
#     def __enter__(self):
#         if not isinstance(_Session, sessionmaker):
#             raise SessionNotInitialisedError
#         self.token = _session.set(_Session(**self.session_args))
#         return type(self)
#
#     def __exit__(self, exc_type, exc_value, traceback):
#         sess = _session.get()
#         if exc_type is not None:
#             sess.rollback()
#
#         if self.commit_on_exit:
#             sess.commit()
#
#         sess.close()
#         _session.reset(self.token)
#
#
# db: DBSessionMeta = DBSession




from contextvars import ContextVar

from panther.logger import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from panther.exceptions import SessionNotInitialisedError, MissingSessionError

# _Session: sessionmaker | None = None
# _session: ContextVar[Session | None] = ContextVar('_session', default=None)

_Session: sessionmaker | None = None

def __session():
    _session = _Session()

    logger.info(f'{hasattr(_session, "add") = }')
    logger.info(f'{hasattr(_session, "session") = }')
    logger.info(f'{_session = }')
    logger.info(f'{type(_session) = }')
    # try:
    #     yield _session
    # finally:
    #     _session.close()
    return _session

session = __session()

def create_session(database_url: str, database_type: str):
    logger.info('create_session')
    if database_type == 'SQLite':
        engine = create_async_engine(database_url)
    else:
        engine = create_engine(database_url)
    _Session: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)




