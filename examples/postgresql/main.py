import os

from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload

from panther import Panther, status
from panther.app import API
from panther.db.connections import db
from panther.request import Request
from panther.response import Response

DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PostgreSQLConnection',
        'url': os.getenv(
            'DATABASE_URL',
            'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/panther_example',
        ),
    },
}


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = 'authors'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    books: Mapped[list['Book']] = relationship(back_populates='author', cascade='all, delete-orphan')


class Book(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.id'))
    author: Mapped[Author] = relationship(back_populates='books')


class AuthorInput(BaseModel):
    name: str = Field(min_length=1)


class AuthorUpdate(BaseModel):
    name: str = Field(min_length=1)


class BookInput(BaseModel):
    title: str = Field(min_length=1)


class BookOutput(BaseModel):
    id: int
    title: str


class AuthorOutput(BaseModel):
    id: int
    name: str
    books: list[BookOutput]


class AuthorPageOutput(BaseModel):
    items: list[AuthorOutput]
    next_cursor: int | None


class AuthorSummaryOutput(BaseModel):
    id: int
    name: str


def serialize_author(author: Author) -> dict:
    return AuthorOutput(
        id=author.id,
        name=author.name,
        books=[BookOutput(id=book.id, title=book.title) for book in author.books],
    ).model_dump()


@API(methods=['GET'])
async def list_author_summaries_with_raw_sql(request: Request):
    limit = min(max(int(request.query_params.get('limit', 20)), 1), 100)
    statement = text('SELECT id, name FROM authors ORDER BY id LIMIT :limit')

    async with db.session_context() as session:
        rows = await session.execute(statement, {'limit': limit})
        authors = [AuthorSummaryOutput(**row).model_dump() for row in rows.mappings()]

    return authors


@API(methods=['POST'], input_model=AuthorInput)
async def create_author(request: Request):
    async with db.session_context() as session:
        author = Author(**request.validated_data.model_dump())
        session.add(author)
        await session.commit()
        return Response(data={'id': author.id, 'name': author.name}, status_code=status.HTTP_201_CREATED)


@API(methods=['GET'])
async def list_authors(request: Request):
    limit = min(max(int(request.query_params.get('limit', 20)), 1), 100)
    cursor = request.query_params.get('cursor')
    statement = select(Author).options(selectinload(Author.books)).order_by(Author.id).limit(limit + 1)
    if cursor:
        statement = statement.where(Author.id > int(cursor))

    async with db.session_context() as session:
        authors = list((await session.execute(statement)).scalars())

    has_next_page = len(authors) > limit
    authors = authors[:limit]
    return AuthorPageOutput(
        items=[AuthorOutput(**serialize_author(author)) for author in authors],
        next_cursor=authors[-1].id if has_next_page else None,
    ).model_dump()


@API(methods=['GET'])
async def get_author(author_id: int):
    statement = select(Author).options(selectinload(Author.books)).where(Author.id == author_id)
    async with db.session_context() as session:
        author = (await session.execute(statement)).scalar_one_or_none()

    if author is None:
        return Response(data={'detail': 'Author not found'}, status_code=status.HTTP_404_NOT_FOUND)
    return serialize_author(author)


@API(methods=['PUT'], input_model=AuthorUpdate)
async def update_author(request: Request, author_id: int):
    async with db.session_context() as session:
        author = await session.get(Author, author_id)
        if author is None:
            return Response(data={'detail': 'Author not found'}, status_code=status.HTTP_404_NOT_FOUND)
        author.name = request.validated_data.name
        await session.commit()
        return {'id': author.id, 'name': author.name}


@API(methods=['DELETE'])
async def delete_author(author_id: int):
    async with db.session_context() as session:
        author = await session.get(Author, author_id)
        if author is None:
            return Response(data={'detail': 'Author not found'}, status_code=status.HTTP_404_NOT_FOUND)
        await session.delete(author)
        await session.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@API(methods=['POST'], input_model=BookInput)
async def create_book(request: Request, author_id: int):
    async with db.session_context() as session:
        author = await session.get(Author, author_id)
        if author is None:
            return Response(data={'detail': 'Author not found'}, status_code=status.HTTP_404_NOT_FOUND)
        book = Book(author=author, **request.validated_data.model_dump())
        session.add(book)
        await session.commit()
        return Response(data={'id': book.id, 'title': book.title}, status_code=status.HTTP_201_CREATED)


url_routing = {
    'authors/': list_authors,
    'authors/raw/': list_author_summaries_with_raw_sql,
    'authors/create/': create_author,
    'authors/<author_id>/': get_author,
    'authors/<author_id>/update/': update_author,
    'authors/<author_id>/delete/': delete_author,
    'authors/<author_id>/books/create/': create_book,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
