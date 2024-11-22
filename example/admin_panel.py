import http.cookies
import string
import random
from pydantic import BaseModel

from panther import Panther
from panther.app import API
from panther.base_websocket import Websocket
from panther.db import Model
from panther.panel.urls import urls as admin_url
from panther.authentications import BaseAuthentication
from panther.request import Request


cookie: http.cookies.BaseCookie[str] = http.cookies.SimpleCookie()


class Book(BaseModel):
    title: str
    pages_count: int



class Person(BaseModel):
    age: int
    real_name: str


class Author(Model):
    name: str
    person: Person | None = None
    books: list[Book]
    is_male: bool | None


@API()
async def generate_data():
    for _ in range(10):
        await Author.insert_one(
            name=''.join(random.choices(string.ascii_lowercase, k=10)),
            books=[Book(title='Book1', pages_count=10).model_dump(), Book(title='Book1', pages_count=10).model_dump()],
            is_male=False,
        )


DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
    }
}

app = Panther(__name__, configs=__name__, urls={'admin': admin_url, 'generate': generate_data})
