import typing
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import jinja2
from pydantic import BaseModel as PydanticBaseModel


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
        self.life_time = int(life_time.total_seconds()) if isinstance(life_time, timedelta) else life_time

        if refresh_life_time:
            if isinstance(refresh_life_time, timedelta):
                self.refresh_life_time = refresh_life_time.total_seconds()
            else:
                self.refresh_life_time = refresh_life_time
        else:
            self.refresh_life_time = self.life_time * 2

    def __eq__(self, other):
        return bool(
            self.key == other.key
            and self.algorithm == other.algorithm
            and self.life_time == other.life_time
            and self.refresh_life_time == other.refresh_life_time,
        )


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
    BASE_DIR: Path = Path()
    MONITORING: bool = False
    LOG_QUERIES: bool = False
    THROTTLING = None  # type: panther.throttling.Throttle
    SECRET_KEY: str | None = None
    HTTP_MIDDLEWARES: list = field(default_factory=list)
    WS_MIDDLEWARES: list = field(default_factory=list)
    USER_MODEL: type[PydanticBaseModel] | None = None
    AUTHENTICATION: type[PydanticBaseModel] | None = None
    WS_AUTHENTICATION: type[PydanticBaseModel] | None = None
    JWT_CONFIG: JWTConfig | None = None
    MODELS: list = field(default_factory=list)
    FLAT_URLS: dict = field(default_factory=dict)
    URLS: dict = field(default_factory=dict)
    WEBSOCKET_CONNECTIONS: Callable | None = None
    BACKGROUND_TASKS: bool = False
    HAS_WS: bool = False
    TIMEZONE: str = 'UTC'
    TEMPLATES_DIR: str | list[str] = '.'
    JINJA_ENVIRONMENT: jinja2.Environment | None = None
    AUTO_REFORMAT: bool = False
    QUERY_ENGINE: Callable | None = None
    DATABASE: Callable | None = None

    def refresh(self):
        """
        Reset built-in fields and remove any custom (non-built-in) attributes.
        * In some tests we need to `refresh` the `config` values
        """
        builtin_fields = set(self.__dataclass_fields__)
        current_fields = set(self.__dict__)

        # Reset built-in fields
        for field_name in builtin_fields:
            field_def = self.__dataclass_fields__[field_name]
            default = field_def.default_factory() if callable(field_def.default_factory) else field_def.default
            setattr(self, field_name, default)

        # Delete custom attributes
        for field_name in current_fields - builtin_fields:
            delattr(self, field_name)

    def vars(self) -> dict[str, typing.Any]:
        """Return all config variables (built-in + custom)."""
        return dict(self.__dict__)

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'QUERY_ENGINE' and value:
            QueryObservable.update()

    def __getattr__(self, item: str):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            return None

    def __setitem__(self, key, value):
        setattr(self, key.upper(), value)

    def __getitem__(self, item):
        return getattr(self, item.upper())


config = Config()
