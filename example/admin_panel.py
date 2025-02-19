from __future__ import annotations

import random

from faker.proxy import Faker
from pydantic import BaseModel

from panther import Panther
from panther.app import API
from panther.db import Model
from panther.panel.urls import urls as admin_url

f = Faker()


class Person(BaseModel):
    real_name: str | None = None
    age: int | None = None
    is_alive: bool | None = None


class Book(BaseModel):
    title: str
    pages_count: int
    readers: list[Person] | None = None


class Author(Model):
    name: str
    age: int
    is_male: bool
    person: Person | None = None
    books: list[Book] | None = None


@API()
async def generate_data():
    for i in range(10):
        await Author.insert_one(
            name=f.name(),
            age=random.randint(10, 99),
            is_male=random.getrandbits(1),
            person=Person(
                real_name=f.name(),
                is_alive=random.getrandbits(1),
                age=random.randint(10, 99)
            ).model_dump() if i % 2 else None,
            books=[
                Book(title='Book1', pages_count=10, readers=[Person(
                    real_name=f.name(),
                    is_alive=random.getrandbits(1),
                    age=random.randint(10, 99)
                ).model_dump()]).model_dump(), Book(title='Book1', pages_count=10).model_dump()
            ] if i % 2 else None,
        )


DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
    }
}

app = Panther(__name__, configs=__name__, urls={'admin': admin_url, 'generate': generate_data})
