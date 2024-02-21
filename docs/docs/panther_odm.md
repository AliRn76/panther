  
### find_one  
Get a single document from the database.

```python
from app.models import User

user: User = await User.find_one(id=1, name='Ali')
or
user: User = await User.find_one({'id': 1, 'name': 'Ali'})
or
user: User = await User.find_one({'id': 1}, name='Ali')
```

### find  
Get documents from the database.

```python  
users: list[User] = await User.find(age=18, name='Ali')
or
users: list[User] = await User.find({'age': 18, 'name': 'Ali'})
or
users: list[User] = await User.find({'age': 18}, name='Ali')
```  

### all
Get all documents from the database. (Alias of `.find()`)
  
```python  
users: list[User] = User.all()
```

### first
Get the first document from the database.
  
```python  
from app.models import User

user: User = await User.first(age=18, name='Ali')
or
user: User = await User.first({'age': 18, 'name': 'Ali'})
or
user: User = await User.first({'age': 18}, name='Ali')
```  

### last
Get the last document from the database.
  
```python  
from app.models import User

user: User = await User.last(age=18, name='Ali')
or
user: User = await User.last({'age': 18, 'name': 'Ali'})
or
user: User = await User.last({'age': 18}, name='Ali')
```

### aggregate
Perform an aggregation using the aggregation framework on this collection.
> Only available in mongodb
  
```python  
from typing import Iterable
from app.models import User

pipeline = [
    {'$match': {...}},
    {'$unwind': ...},
    {'$group': {...}},
    {'$project': {...}},
    {'$sort': {...}}
    ...
]
users: Iterable[dict] = await User.aggregate(pipeline)
```  

### count  
Count the number of documents in this collection.
  
```python  
from app.models import User

users_count: int = await User.count(age=18, name='Ali')
or
users_count: int = await User.count({'age': 18, 'name': 'Ali'})
or
users_count: int = await User.count({'age': 18}, name='Ali')
```

### insert_one  
Insert a single document.
  
```python  
from app.models import User

user: User = await User.insert_one(age=18, name='Ali')
or
user: User = await User.insert_one({'age': 18, 'name': 'Ali'})
or
user: User = await User.insert_one({'age': 18}, name='Ali')
```

### insert_many  
Insert an iterable of documents.
  
```python  
from app.models import User

users = [
    {'age': 18, 'name': 'Ali'},
    {'age': 17, 'name': 'Saba'},
    {'age': 16, 'name': 'Amin'}
]

users: list[User] = await User.insert_many(users)
```

### delete  
Delete the document.
  
```python  
from app.models import User

user = await User.find_one(name='Ali')

await user.delete()
```

### delete_one  
Delete a single document matching the filter.
  
```python  
from app.models import User

is_deleted: bool = await User.delete_one(age=18, name='Ali')
or
is_deleted: bool = await User.delete_one({'age': 18, 'name': 'Ali'})
or
is_deleted: bool = await User.delete_one({'age': 18}, name='Ali')
```

### delete_many  
Delete one or more documents matching the filter.
  
```python  
from app.models import User

deleted_count: int = await User.delete_many(age=18, name='Ali')
or
deleted_count: int = await User.delete_many({'age': 18, 'name': 'Ali'})
or
deleted_count: int = await User.delete_many({'age': 18}, name='Ali')
```

### update  
Update the document.
  
```python  
from app.models import User

user = await User.find_one(age=18, name='Ali')

await user.update(name='Saba', age=19)
or
await user.update({'name': 'Saba'}, age=19)
or
await user.update({'name': 'Saba', 'age': 19})
```

### update_one  
Update a single document matching the filter.

- You have to filter with a `dictionary` as `first parameter`
- Then pass your new parameters
  
```python  
from app.models import User

query = {'id': 1}

is_updated: bool = await User.update_one(query, age=18, name='Ali')
or
is_updated: bool = await User.update_one(query, {'age': 18, 'name': 'Ali'})
or
is_updated: bool = await User.update_one(query, {'age': 18}, name='Ali')
```

### update_many  
Update one or more documents that match the filter.

- You have to filter with a `dictionary` as `first parameter`
- Then pass your new parameters

```python
from app.models import User

query = {'name': 'Saba'}

updated_count: int = await User.update_many(query, age=18, name='Ali')
or
updated_count: int = await User.update_many(query, {'age': 18, 'name': 'Ali'})
or
updated_count: int = await User.update_many(query, {'age': 18}, name='Ali')
```

### find_one_or_insert 
- Get a single document from the database 
  - **or** 
- Insert a single document
  
```python  
from app.models import User

is_inserted, user = await User.find_one_or_insert(age=18, name='Ali')
or
is_inserted, user = await User.find_one_or_insert({'age': 18, 'name': 'Ali'})
or
is_inserted, user = await User.find_one_or_insert({'age': 18}, name='Ali')
```

### find_one_or_raise
- Get a single document from the database]
  - **or** 
- Raise an `APIError(f'{Model} Does Not Exist')`
  
```python  
from app.models import User

user: User = await User.find_one_or_raise(age=18, name='Ali')
or
user: User = await User.find_one_or_raise({'age': 18, 'name': 'Ali'})
or
user: User = await User.find_one_or_raise({'age': 18}, name='Ali')
```

### save
Save the document.
- If it has id --> `Update` It
- else --> `Insert` It

```python  
from app.models import User

# Update
user = await User.find_one(name='Ali')
user.name = 'Saba'
await user.save()

# Insert
user = User(name='Ali')
await user.save()
```