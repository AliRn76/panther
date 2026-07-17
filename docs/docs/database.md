# Database Support in Panther

Panther natively supports two document databases: `MongoDB` and `PantherDB`. However, you can also define your own custom database connections and queries.

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
- All values in `engine` (except `class`) are passed to the `__init__` method of the specified class.
- The `query` key is optional for the default supported engines, but you can customize it if needed.

## Custom Backends

Custom engines should subclass `panther.db.connections.BaseDatabaseConnection` and implement the `session` property. They can return their query implementation from `get_query_engine()`; alternatively, set the existing `query` configuration value explicitly.

Backends declare capabilities rather than requiring Panther to check their concrete class. The built-in document backends use `uses_document_models`; MongoDB additionally uses `uses_object_ids` and `uses_mongo_query_syntax`. A future relational backend can leave these capabilities disabled and provide its own query implementation.

If a backend needs an active event loop to allocate or release resources, implement its async `startup()` and `shutdown()` hooks. Panther invokes them during ASGI lifespan startup and shutdown.

Backends can also override `session_context()` to provide a scoped unit of work. The built-in document backends yield their existing connection; relational backends can create, commit or roll back, and close a session there.

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

## How Does It Work?

- Panther creates a database connection based on the `DATABASE` configuration you define in your configs.
- You can access this connection through your models, or directly via:
  ```python
  from panther.db.connections import db
  ```
