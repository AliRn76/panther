# Database Support in Panther

Panther natively supports `MongoDB`, `PantherDB`, and `PostgreSQL`. You can also define custom database connections and queries.

The built-in `panther.db.Model` is a document model. It remains available for compatibility; `panther.db.DocumentModel` is its explicit name. Relational integrations should provide their own persistence models rather than inheriting from either class.

---

## Configuration Structure

Define your database configuration in the following format:

```python
DATABASE = {
    'engine': {
        'class': 'address of engine',
        'arg1': 'value1',
        # ... additional arguments ...
    },
    'query': 'address of query class',  # Optional
}
```

### Notes
- **Built-in supported engines:**
  - `panther.db.connections.PantherDBConnection`
  - `panther.db.connections.MongoDBConnection`
  - `panther.db.connections.PostgreSQLConnection`
- All values in `engine` (except `class`) are passed to the `__init__` method of the specified class.
- The `query` key is optional for the default supported engines, but you can customize it if needed.

## Custom Backends

Custom engines should subclass `panther.db.connections.BaseDatabaseConnection` and implement the `session` property. They can return their query implementation from `get_query_engine()`; alternatively, set the existing `query` configuration value explicitly.

Query implementations must subclass `panther.db.queries.base_queries.BaseQuery`.

Backends declare capabilities rather than requiring Panther to check their concrete class. The built-in document backends use `uses_document_models`; MongoDB additionally uses `uses_object_ids` and `uses_mongo_query_syntax`. Relational backends leave these capabilities disabled and do not use the document query API.

If a backend needs an active event loop to allocate or release resources, implement its async `startup()` and `shutdown()` hooks. Panther invokes them during ASGI lifespan startup and shutdown.

Backends can also override `session_context()` to provide a scoped unit of work. The built-in document backends yield their existing connection; relational backends can create, commit or roll back, and close a session there. Code that needs a scoped session can use `db.session_context()`.

```python
from contextlib import asynccontextmanager

from panther.db.connections import BaseDatabaseConnection, db


class SQLConnection(BaseDatabaseConnection):
    def init(self, session_factory):
        self._session_factory = session_factory

    @property
    def session(self):
        return self._session_factory

    @asynccontextmanager
    async def session_context(self):
        async with self._session_factory() as session:
            yield session


async with db.session_context() as session:
    # Use the backend's scoped session.
    pass
```

---

## PantherDB

Example configuration for PantherDB:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': BASE_DIR / 'database.pdb',  # Optional
        'encryption': True  # Optional, default is False
    }
}
```

### Notes
- `path` is optional; you can customize the directory and filename of your database.
- `encryption` is optional and defaults to `False`.
- The `cryptography` package is required if you set `encryption` to `True`.

---

## MongoDB

Example configuration for MongoDB:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.MongoDBConnection',
        'host': 'mongodb://127.0.0.1:27017/database_name'
    }
}
```

### Notes
- The parameters for the engine are the same as those for `pymongo.MongoClient`. See the [PyMongo documentation](https://pymongo.readthedocs.io/en/stable/tutorial.html#making-a-connection-with-mongoclient) for details.

---

## PostgreSQL

Install the optional PostgreSQL dependencies:

```bash
pip install 'panther[postgresql]'
```

Configure Panther with a SQLAlchemy async URL:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PostgreSQLConnection',
        'url': 'postgresql+asyncpg://postgres:password@127.0.0.1:5432/my_database',
        'echo': False,  # Optional SQLAlchemy engine setting
    },
}
```

`PostgreSQLConnection` validates the engine configuration while Panther loads settings. During ASGI startup, Panther opens a connection and runs a health check; invalid credentials, hosts, or database names prevent the application from serving requests.

### Define SQLAlchemy models

PostgreSQL applications use ordinary SQLAlchemy declarative models. Do not inherit from `panther.db.DocumentModel` or use document query methods such as `find()`.

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
```

### Use sessions explicitly

`db.session` is the SQLAlchemy session factory. Prefer `db.session_context()` so every unit of work receives a new session and failures are rolled back automatically. Successful writes require an explicit commit.

```python
from sqlalchemy import select

from panther.db.connections import db


async def create_and_list_users(name: str) -> list[User]:
    async with db.session_context() as session:
        session.add(User(name=name))
        await session.commit()

        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars())
```

Panther disposes the connection pool during ASGI shutdown.

Use `sqlalchemy.text()` for raw SQL and bind external values as parameters rather than formatting them into the query string:

```python
from sqlalchemy import text


async with db.session_context() as session:
    result = await session.execute(
        text('SELECT id, name FROM users WHERE id = :user_id'),
        {'user_id': user_id},
    )
    user = result.mappings().one_or_none()
```

For a complete CRUD, relationship, and cursor-pagination example, see the `examples/postgresql` directory in the Panther repository.

---

## How Does It Work?

- Panther creates a database connection based on the `DATABASE` configuration you define in your configs.
- You can access this connection through your models, or directly via:
  ```python
  from panther.db.connections import db
  ```
