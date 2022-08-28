from typing import TypedDict


class Config(TypedDict):
    debug: bool
    urls: dict
    middlewares: list
    db_engine: str


config: Config = {
    'debug': False,
    'urls': {},
    'middlewares': [],
    'db_engine': '',
}
