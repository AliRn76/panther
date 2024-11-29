from __future__ import annotations

import http.cookies
import string
import random
from pydantic import BaseModel

from panther import Panther
from panther.app import API
from panther.db import Model
from panther.panel.urls import urls as admin_url


cookie: http.cookies.BaseCookie[str] = http.cookies.SimpleCookie()


class Book(BaseModel):
    title: str
    pages_count: int
    readers: list[Person]
    co_owner: Person


class Parent(BaseModel):
    name: str
    age: str
    has_child: bool

class Person(BaseModel):
    age: int
    real_name: str
    parent: Parent
    is_alive: bool
    friends: list[Person]



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
