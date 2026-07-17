# PostgreSQL API Example

This example uses Panther with normal SQLAlchemy models, PostgreSQL, and explicit session commits. It does not use `DocumentModel`, document query methods, generic document CRUD APIs, or the Panther admin panel.

## Run locally

Start PostgreSQL:

```bash
docker run --rm -p 5432:5432 -d --name postgres \
  -e POSTGRES_DB=panther_example -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres postgres:16
```

Install Panther with PostgreSQL support and start the application:

```bash
pip install 'panther[postgresql]'
panther run main:app --reload
```

Set `DATABASE_URL` when your database does not use the default local connection string.

Create the `authors` and `books` tables with Alembic before starting the application. See the [PostgreSQL migrations guide](../../docs/docs/postgresql_migrations.md).

## API patterns

- `POST /authors/create/` creates an author and explicitly commits.
- `GET /authors/?limit=20&cursor=10` uses cursor pagination and `selectinload` to fetch authors with books efficiently.
- `GET /authors/raw/?limit=20` executes a parameterized raw SQL query with `sqlalchemy.text()`.
- `GET`, `PUT`, and `DELETE /authors/<author_id>/` show read, update, and delete operations.
- `POST /authors/<author_id>/books/create/` creates a related record in an explicit transaction.
