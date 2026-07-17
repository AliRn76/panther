# PostgreSQL Migrations

Panther uses [Alembic](https://alembic.sqlalchemy.org/) for PostgreSQL schema migrations. Alembic owns schema history; Panther does not generate or apply migrations during application startup.

Install PostgreSQL support, including Alembic:

```bash
pip install 'panther[postgresql]'
```

## Initialize Alembic

Run this once from the project root:

```bash
alembic init -t async migrations
```

Set the async SQLAlchemy URL in `alembic.ini`:

```ini
sqlalchemy.url = postgresql+asyncpg://postgres:password@127.0.0.1:5432/my_database
```

The URL should match the one configured for `PostgreSQLConnection` in Panther.

## Register model metadata

Alembic needs the metadata from your SQLAlchemy declarative base to generate migrations. In `migrations/env.py`, import the base after the generated imports and assign its metadata:

```python
from app.models import Base

target_metadata = Base.metadata
```

For example, application models can share this base:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
```

Import every module that declares models before Alembic reads `Base.metadata`; otherwise, autogeneration cannot see those tables.

## Create and apply migrations

Generate a revision after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m 'create users'
```

Review the generated migration, then apply it:

```bash
alembic upgrade head
```

To revert the latest revision during development:

```bash
alembic downgrade -1
```

Run `alembic upgrade head` as a deployment step before starting Panther. Do not rely on application startup to modify production schemas.
