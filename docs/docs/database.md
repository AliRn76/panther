Panther currently built-in supports 2 database (`MongoDB`, `PantherDB`), but you can define your own custom database connection and queries too.


### Structure

```python
DATABASE = {
    'engine': {
        'class': 'address of engine',
        'arg1': 'value1',
        ...
    },
    'query': 'address of query class'
}
```
#### Notes
- Built-in supported engines:
  - `panther.db.connections.PantherDBConnection`
  - `panther.db.connections.MongoDBConnection`
- `engine` values, other than the `class` will be passed to the `class.__init__()` 
- `query` is not required when you are using default supported engines, but you can customize it

### PantherDB

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': BASE_DIR / 'database.pdb',
        'encryption': True
    }
}
```

#### Notes
- `path` is not required, but you can customize the directory and file of your database
- `encryption` is not required and default is `False`
- The `cryptography` package is required if you set `encryption` to `True`

### MongoDB

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.MongoDBConnection',
        'host': 'mongodb://127.0.0.1:27017/database_name'
    }
}
```

#### Notes
- The parameters are same as `pymongo.MongoClient` [[Reference]](https://pymongo.readthedocs.io/en/stable/tutorial.html#making-a-connection-with-mongoclient)

### How it works?

- Panther creates a database connection depends on `DATABASE` block you defined in `configs`

- You can access to this connection with your `models`,
or direct access from `from panther.db.connections import db`


- Now we are going to create a new API which uses `PantherDB` and creating a `Book`

  1.  Create `Book` model in `app/models.py`
      ```python  
      from panther.db import Model
    
    
      class Book(Model):
          title: str
          description: str
          pages_count: int
      ```

  2. Add `book` url in `app/urls.py` that points to `book_api()`

      ```python  
      ...
      from app.apis import book_api
    
    
      urls = {
          'book/': book_api,
      }
      ```  

  3. Create `book_api()` in `app/apis.py`

      ```python  
      from panther import status
      from panther.app import API
      from panther.response import Response
    
    
      @API()
      async def book_api():
          ...
          return Response(status_code=status.HTTP_201_CREATED)  
      ```  

  4. Now we should use the [Panther ODM](https://pantherpy.github.io/panther_odm/) to create a book, it's based on mongo queries, for creation we use `insert_one` like this:

      ```python
      from panther import status
      from panther.app import API
      from panther.response import Response
      from app.models import Book
    
    
      @API()
      async def book_api():
          Book.insert_one(
              title='Python',
              description='Python is good.',
              pages_count=10
          )
          return Response(status_code=status.HTTP_201_CREATED)  
      ```

**In [next](https://pantherpy.github.io/panther_odm/) step we are going to explain more about `Panther ODM`**
