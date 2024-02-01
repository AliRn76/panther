import typing
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable

from pydantic._internal._model_construction import ModelMetaclass

from panther.throttling import Throttling
from panther.utils import Singleton


class JWTConfig:
    def __init__(
            self,
            key: str,
            algorithm: str = 'HS256',
            life_time: timedelta | int = timedelta(days=1),
            refresh_life_time: timedelta | int | None = None,
    ):
        self.key = key
        self.algorithm = algorithm
        self.life_time = life_time.total_seconds() if isinstance(life_time, timedelta) else life_time

        if refresh_life_time:
            if isinstance(refresh_life_time, timedelta):
                self.refresh_life_time = refresh_life_time.total_seconds()
            else:
                self.refresh_life_time = refresh_life_time
        else:
            self.refresh_life_time = self.life_time * 2


class QueryObservable:
    observers = []

    @classmethod
    def observe(cls, observer):
        cls.observers.append(observer)

    @classmethod
    def update(cls):
        for observer in cls.observers:
            observer._reload_bases(parent=config.query_engine)


@dataclass
class Config(Singleton):
    base_dir: Path
    monitoring: bool
    log_queries: bool
    default_cache_exp: timedelta | None
    throttling: Throttling | None
    secret_key: bytes | None
    http_middlewares: list
    ws_middlewares: list
    reversed_http_middlewares: list
    reversed_ws_middlewares: list
    user_model: ModelMetaclass | None
    authentication: ModelMetaclass | None
    jwt_config: JWTConfig | None
    models: list[dict]
    flat_urls: dict
    urls: dict
    query_engine: typing.Callable | None
    websocket_connections: typing.Callable | None
    background_tasks: bool
    has_ws: bool
    startup: Callable | None
    shutdown: Callable | None
    auto_reformat: bool
    pantherdb_encryption: bool

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'query_engine':
            QueryObservable.update()

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        return getattr(self, item)


config = Config(
    base_dir=Path(),
    monitoring=False,
    log_queries=False,
    default_cache_exp=None,
    throttling=None,
    secret_key=None,
    http_middlewares=[],
    ws_middlewares=[],
    reversed_http_middlewares=[],
    reversed_ws_middlewares=[],
    user_model=None,
    authentication=None,
    jwt_config=None,
    models=[],
    flat_urls={},
    urls={},
    query_engine=None,
    websocket_connections=None,
    background_tasks=False,
    has_ws=False,
    startup=None,
    shutdown=None,
    auto_reformat=False,
    pantherdb_encryption=False,
)
