from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import TypedDict

from pydantic.main import ModelMetaclass


@dataclass(frozen=True)
class JWTConfig:
    key: str
    algorithm: str = 'HS256'
    life_time: timedelta | int = timedelta(days=1)


class Config(TypedDict):
    base_dir: Path
    debug: bool
    monitoring: bool
    urls: dict
    middlewares: list
    reversed_middlewares: list
    db_engine: str
    default_cache_exp: timedelta | None
    secret_key: str
    authentication: ModelMetaclass | None
    jwt_config: JWTConfig | None
    user_model: ModelMetaclass | None


config: Config = {
    'base_dir': Path(),
    'debug': False,
    'monitoring': True,
    'secret_key': '',
    'urls': {},
    'middlewares': [],
    'reversed_middlewares': [],
    'db_engine': '',
    'default_cache_exp': None,
    'jwt_config': None,
    'authentication': None,
    'user_model': None,
}
