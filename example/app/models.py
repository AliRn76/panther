from typing import List

from pydantic import BaseModel

from panther.db import Model
from panther.db.models import BaseUser
from panther.events import Event


class CustomQuery:
    @classmethod
    def find_last(cls):
        return cls.last()


class User(BaseUser, CustomQuery):
    username: str
    password: str


class Book(Model):
    name: str


class BookDetail(BaseModel):
    detail: str
    book: Book
    more_books: list[list[Book]]


class Author(Model):
    name: str
    books: list[Book]
    books2: List[Book]
    # new_book: dict[str, Book]
    book: Book
    book2: None | Book = None
    book_detail: dict
    our_book_detail: BookDetail
    #


@Event.startup
async def create_author():
    b2 = await Book.insert_one(name='test1')
    print(f'{b2=}')
    # b2 = Book(_id=ObjectId('6823ab43deda8ab1ee0394a6'), name='test1')
    # # try:
    # a1 = Author(name='ali', books=[b1.model_dump()])
    a1 = await Author.insert_one(
        name='ali12',
        books=[b2],
        books2=[b2, b2],
        # new_book={'b': b2},
        book=b2,
        book2=None,
        book_detail={'book1': b2},
        our_book_detail=BookDetail(detail='ok', book=b2, more_books=[[b2, b2]]),
    )
    print(f'{a1=}')
    # # await a1.save()
    # print(f'{a1=}')
    # # except Exception as e:
    # #     print(f'{e=}')
    # #     raise e
    # a2 = await Author.find_one(name='ali12')
    # print(f'{list(a2)=}')
