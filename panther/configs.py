from datetime import timedelta
from typing import TypedDict
from pathlib import Path


class Config(TypedDict):
    base_dir: Path
    debug: bool
    urls: dict
    middlewares: list
    db_engine: str
    default_cache_exp: timedelta | None


# TODO: make it class or something that we can access to the attr with dot
config: Config = {
    'base_dir': Path(),
    'debug': False,
    'urls': {},
    'middlewares': [],
    'db_engine': '',
    'default_cache_exp': None,
}
