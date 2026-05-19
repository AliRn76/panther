from pydantic import BaseModel, Field

from panther import Panther, status
from panther.app import API
from panther.request import Request
from panther.response import Response


class CreateBookInput(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    pages_count: int = Field(ge=1)


class BookOutput(BaseModel):
    title: str
    author: str


BOOKS: list[dict] = [
    {'id': 1, 'title': 'Panther Guide', 'author': 'Panther Team', 'pages_count': 120},
]


@API(methods=['GET'])
async def list_books(request: Request):
    author = request.query_params.get('author')
    if author:
        return [book for book in BOOKS if book['author'] == author]
    return BOOKS


@API(methods=['GET'], output_model=BookOutput)
async def first_book():
    return BOOKS[0]


@API(methods=['GET'])
async def get_book(book_id: int):
    for book in BOOKS:
        if book['id'] == book_id:
            return book
    return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_404_NOT_FOUND)


@API(methods=['POST'], input_model=CreateBookInput)
async def create_book(request: Request):
    book = {'id': len(BOOKS) + 1, **request.validated_data.model_dump()}
    BOOKS.append(book)
    return Response(data=book, status_code=status.HTTP_201_CREATED)


url_routing = {
    'books/': list_books,
    'books/create/': create_book,
    'books/first/': first_book,
    'books/<book_id>/': get_book,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
