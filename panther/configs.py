import copy
import typing
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable

import jinja2
from pydantic._internal._model_construction import ModelMetaclass

from panther.throttling import Throttling


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
            observer._reload_bases(parent=config.QUERY_ENGINE)


@dataclass
class Config:
    BASE_DIR: Path
    MONITORING: bool
    LOG_QUERIES: bool
    DEFAULT_CACHE_EXP: timedelta | None
    THROTTLING: Throttling | None
    SECRET_KEY: bytes | None
    HTTP_MIDDLEWARES: list[tuple]
    WS_MIDDLEWARES: list[tuple]
    USER_MODEL: ModelMetaclass | None
    AUTHENTICATION: ModelMetaclass | None
    WS_AUTHENTICATION: ModelMetaclass | None
    JWT_CONFIG: JWTConfig | None
    MODELS: list[dict]
    FLAT_URLS: dict
    URLS: dict
    WEBSOCKET_CONNECTIONS: typing.Callable | None
    BACKGROUND_TASKS: bool
    HAS_WS: bool
    STARTUPS: list[Callable]
    SHUTDOWNS: list[Callable]
    TIMEZONE: str
    TEMPLATES_DIR: str | list[str]
    JINJA_ENVIRONMENT: jinja2.Environment | None
    AUTO_REFORMAT: bool
    QUERY_ENGINE: typing.Callable | None
    DATABASE: typing.Callable | None

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'QUERY_ENGINE' and value:
            QueryObservable.update()

    def __setitem__(self, key, value):
        setattr(self, key.upper(), value)

    def __getitem__(self, item):
        return getattr(self, item.upper())

    def refresh(self):
        # In some tests we need to `refresh` the `config` values
        for key, value in copy.deepcopy(default_configs).items():
            setattr(self, key, value)


default_configs = {
    'BASE_DIR': Path(),
    'MONITORING': False,
    'LOG_QUERIES': False,
    'DEFAULT_CACHE_EXP': None,
    'THROTTLING': None,
    'SECRET_KEY': None,
    'HTTP_MIDDLEWARES': [],
    'WS_MIDDLEWARES': [],
    'USER_MODEL': None,
    'AUTHENTICATION': None,
    'WS_AUTHENTICATION': None,
    'JWT_CONFIG': None,
    'MODELS': [],
    'FLAT_URLS': {},
    'URLS': {},
    'WEBSOCKET_CONNECTIONS': None,
    'BACKGROUND_TASKS': False,
    'HAS_WS': False,
    'STARTUPS': [],
    'SHUTDOWNS': [],
    'TIMEZONE': 'UTC',
    'TEMPLATES_DIR': '.',
    'JINJA_ENVIRONMENT': None,
    'AUTO_REFORMAT': False,
    'QUERY_ENGINE': None,
    'DATABASE': None,
}

config = Config(**copy.deepcopy(default_configs))
