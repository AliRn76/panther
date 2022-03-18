from dataclasses import dataclass


SupportedDatabase = ('MySQL', 'PostgreSQL', 'SQLite')

@dataclass
class Database:
    host: str
    port: int
    username: str
    password: str
    driver: str
    url: str
