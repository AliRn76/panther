from pathlib import Path
from typing import TypedDict
from datetime import timedelta
from dataclasses import dataclass
from pydantic.main import ModelMetaclass

from panther.throttling import Throttling


@dataclass(frozen=True)
class JWTConfig:
    key: str
    algorithm: str = 'HS256'
    life_time: timedelta | int = timedelta(days=1)


class Config(TypedDict):
    base_dir: Path
    monitoring: bool
    log_queries: bool
    urls: dict
    middlewares: list
    reversed_middlewares: list
    db_engine: str
    default_cache_exp: timedelta | None
    secret_key: bytes | None
    authentication: ModelMetaclass | None
    jwt_config: JWTConfig | None
    user_model: ModelMetaclass | None
    throttling: Throttling | None


config: Config = {
    'base_dir': Path(),
    'monitoring': False,
    'log_queries': False,
    'secret_key': None,
    'urls': {},
    'middlewares': [],
    'reversed_middlewares': [],
    'db_engine': '',
    'default_cache_exp': None,
    'jwt_config': None,
    'authentication': None,
    'user_model': None,
    'throttling': None,
}
