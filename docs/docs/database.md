# Database Support in Panther

Panther natively supports `PantherDB`, `MongoDB`, and `SQLite`. However, you can also define your own custom database connections and queries.

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
  - `panther.db.connections.SQLiteConnection`
- All values in `engine` (except `class`) are passed to the `__init__` method of the specified class.
- The `query` key is optional for the default supported engines, but you can customize it if needed.

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

## SQLite

SQLite support is available through the optional SQL dependency:

```bash
pip install "panther[sql]"
```

Example configuration:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.SQLiteConnection',
        'path': BASE_DIR / 'database.sqlite3',
    }
}
```

Create tables for your registered models during startup:

```python
from panther.events import Event
from panther.db.connections import db


@Event.startup
async def create_tables():
    await db.session.create_tables()
```

### Notes

- SQLite uses the same `panther.db.Model` CRUD methods as PantherDB and MongoDB.
- The first SQLite backend supports equality filters only, such as `User.find(username='ali')`.
- `aggregate()` and Mongo-style update operators are not supported.
- `Model`-typed fields are stored as foreign keys and hydrated as related model instances.
- Table creation is supported, but migrations are not included.

---

## How Does It Work?

- Panther creates a database connection based on the `DATABASE` configuration you define in your configs.
- You can access this connection through your models, or directly via:
  ```python
  from panther.db.connections import db
  ```
