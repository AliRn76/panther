from pydantic.main import ModelMetaclass
from dataclasses import dataclass
from datetime import timedelta
from typing import TypedDict
from pathlib import Path


@dataclass(frozen=True)
class JWTConfig:
    key: str
    algorithm: str = 'HS256'
    life_time: timedelta | int = timedelta(days=1)


class Config(TypedDict):
    base_dir: Path
    debug: bool
    urls: dict
    middlewares: list
    db_engine: str
    default_cache_exp: timedelta | None
    secret_key: str
    authentication: str | None
    jwt_config: JWTConfig | None
    user_model: ModelMetaclass | None


# TODO: make it class or something that we can access to the attr with dot
config: Config = {
    'base_dir': Path(),
    'debug': False,
    'secret_key': '',
    'urls': {},
    'middlewares': [],
    'db_engine': '',
    'default_cache_exp': None,
    'jwt_config': None,
    'authentication': None,
    'user_model': None,
}
