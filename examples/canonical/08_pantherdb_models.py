from pathlib import Path

from pydantic import Field

from panther import Panther, status
from panther.app import API
from panther.db import Model
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer

DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': str(Path(__file__).resolve().parent / 'canonical_books.pdb'),
    },
}


class Book(Model):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    pages_count: int = Field(ge=1)


class BookSerializer(ModelSerializer):
    class Config:
        model = Book
        fields = ['title', 'author', 'pages_count']
        required_fields = ['title', 'author', 'pages_count']


@API(methods=['GET'])
async def list_books():
    return await Book.find()


@API(methods=['POST'], input_model=BookSerializer)
async def create_book(request: Request):
    book = await Book.insert_one(request.validated_data.model_dump())
    return Response(data=book, status_code=status.HTTP_201_CREATED)


@API(methods=['GET'])
async def get_book(book_id: str):
    book = await Book.find_one(id=book_id)
    if book is None:
        return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_404_NOT_FOUND)
    return book


url_routing = {
    'books/': list_books,
    'books/create/': create_book,
    'books/<book_id>/': get_book,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
