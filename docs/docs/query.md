# Querying Documents

Panther ODM provides a simple, async interface for interacting with your database models. This guide covers the most common operations.

---

### find_one

Get a single document matching the filter.

```python
from app.models import User

user: User = await User.find_one(id=1, name='Ali')
# or
user: User = await User.find_one({'id': 1, 'name': 'Ali'})
```

- **Returns:** An instance of the model or `None` if not found.

---

### find

Get multiple documents matching the filter.

```python
users: Cursor = await User.find(age=18, name='Ali')
```

- **Returns:** A `Cursor` object (see [Cursor Usage](#cursor-usage)).

#### Chaining

You can chain `skip()`, `limit()`, and `sort()`:

```python
users: Cursor = await User.find(age=18).skip(10).limit(10).sort([('age', -1)])
```

---

### all

Get all documents in the collection.

```python
users: Cursor = await User.all()
```

---

### first / last

Get the first or last document matching the filter.

```python
user: User = await User.first(age=18)
user: User = await User.last(age=18)
```

---

### aggregate

Perform an aggregation (MongoDB only).

```python
pipeline = [
    {'$match': {...}},
    {'$group': {...}},
    # ...
]
users: Iterable[dict] = await User.aggregate(pipeline)
```

---

### count

Count documents matching the filter.

```python
count: int = await User.count(age=18)
```

---

## Inserting Documents

### insert_one

Insert a single document.

```python
user: User = await User.insert_one(age=18, name='Ali')
```

---

### insert_many

Insert multiple documents.

```python
users = [
    {'age': 18, 'name': 'Ali'},
    {'age': 17, 'name': 'Saba'},
]
users: list[User] = await User.insert_many(users)
```

---

## Updating Documents

### update

Update the current document instance.

```python
user = await User.find_one(name='Ali')
await user.update(name='Saba')
```

---

### update_one / update_many

Update one or more documents matching a filter.

```python
is_updated: bool = await User.update_one({'id': 1}, name='Ali')
updated_count: int = await User.update_many({'name': 'Saba'}, age=18)
```

---

### save

Save the document (insert or update).

```python
user = User(name='Ali')
await user.save()
```

---

## Deleting Documents

### delete

Delete the current document instance.

```python
user = await User.find_one(name='Ali')
await user.delete()
```

---

### delete_one / delete_many

Delete one or more documents matching a filter.

```python
is_deleted: bool = await User.delete_one(age=18)
deleted_count: int = await User.delete_many(age=18)
```

---

## Special Methods

### find_one_or_insert

Get or insert a document.

```python
is_inserted, user = await User.find_one_or_insert(age=18, name='Ali')
```

---

### find_one_or_raise

Get a document or raise `NotFoundAPIError`.

```python
user: User = await User.find_one_or_raise(age=18)
```

---

## Cursor Usage

- The `find()` and `all()` methods return a `Cursor` object.
- You can iterate over it or use it as a list.
- For MongoDB: `from panther.db.cursor import Cursor`
- For PantherDB: `from pantherdb import Cursor`

---

## Notes

- All methods are async unless otherwise noted.
- Filters can be passed as keyword arguments or as a dictionary.
- Some features (like `aggregate`) are only available for MongoDB.
