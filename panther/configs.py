from typing import TypedDict
from pathlib import Path


class Config(TypedDict):
    base_dir: Path
    debug: bool
    urls: dict
    middlewares: list
    db_engine: str


config: Config = {
    'base_dir': Path(),
    'debug': False,
    'urls': {},
    'middlewares': [],
    'db_engine': '',
}
