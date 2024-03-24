We assume you could run the project with [Introduction](https://pantherpy.github.io/#installation)

Now let's write custom APIs for `Create`, `Retrieve`, `Update` and `Delete` a `Book`:

## Structure & Requirements
### Create Model

Create a model named `Book` in `app/models.py`:

```python  
from panther.db import Model


class Book(Model):
    name: str
    author: str
    pages_count: int
```  

### Create API Class

Create the `BookAPI()` in `app/apis.py`:

```python  
from panther.app import GenericAPI


class BookAPI(GenericAPI):
    ... 
```  

> We are going to complete it later ...

### Update URLs

Add the `BookAPI` in `app/urls.py`:

```python  
from app.apis import BookAPI


urls = {
    'book/': BookAPI,
}
```

We assume that the `urls` in `core/urls.py` pointing to `app/urls.py`, like below:

```python  
from app.urls import urls as app_urls


urls = {
    '/': app_urls,
}
```

### Add Database

Add `DATABASE` in `configs`, we are going to add `pantherdb`
> [PantherDB](https://github.com/PantherPy/PantherDB/#readme) is a Simple, File-Base and Document Oriented database

```python
...
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
    }
}
...
```

## APIs
### API - Create a Book

Now we are going to create a book on `POST` request, we need to:

1. Inherit from `CreateAPI`:
    ```python
    from panther.generics import CreateAPI
    
    
    class BookAPI(CreateAPI):
        ...
    ```

2. Create a ModelSerializer in `app/serializers.py`, for `validation` of the `request.data`:

    ```python
    from panther.serializer import ModelSerializer
    from app.models import Book
    
    class BookSerializer(ModelSerializer):
        class Config:
            model = Book
            fields = ['name', 'author', 'pages_count']
    ```

3. Set the created serializer in `BookAPI` as `input_model`:

    ```python
    from panther.app import CreateAPI
    from app.serializers import BookSerializer
    
    
    class BookAPI(CreateAPI):
        input_model = BookSerializer
    ```

It is going to create a `Book` with incoming `request.data` and return that instance to user with status code of `201`


### API - List of Books

Let's return list of books of `GET` method, we need to:

1. Inherit from `ListAPI`
    ```python
    from panther.generics import CreateAPI, ListAPI
    from app.serializers import BookSerializer
        
    class BookAPI(CreateAPI, ListAPI):
        input_model = BookSerializer
        ...
    ```

2. define `objects` method, so the `ListAPI` knows to return which books

    ```python
    from panther.generics import CreateAPI, ListAPI
    from panther.request import Request
    
    from app.models import Book
    from app.serializers import BookSerializer
        
    class BookAPI(CreateAPI, ListAPI):
        input_model = BookSerializer
    
        async def objects(self, request: Request, **kwargs):
            return await Book.find()
    ```

### Pagination, Search, Filter, Sort

#### Pagination

Use `panther.pagination.Pagination` as `pagination`

**Usage:** It will look for the `limit` and `skip` in the `query params` and return its own response template

**Example:** `?limit=10&skip=20`

--- 

#### Search

Define the fields you want the search, query on them in `search_fields` 

The value of `search_fields` should be `list`

**Usage:** It works with `search` query param --> `?search=maybe_name_of_the_book_or_author`

**Example:** `?search=maybe_name_of_the_book_or_author`

---

#### Filter

Define the fields you want to be filterable in `filter_fields` 

The value of `filter_fields` should be `list`

**Usage:** It will look for each value of the `filter_fields` in the `query params` and query on them

**Example:** `?name=name_of_the_book&author=author_of_the_book`

---


#### Sort

Define the fields you want to be sortable in `sort_fields` 

The value of `sort_fields` should be `list`



**Usage:** It will look for each value of the `sort_fields` in the `query params` and sort with them

**Example:** `?sort=pages_count,-name`

**Notice:**
   - fields should be separated with a column `,`
   - use `field_name` for ascending sort
   - use `-field_name` for descending sort
---

#### Example
```python
from panther.generics import CreateAPI, ListAPI
from panther.pagination import Pagination
from panther.request import Request

from app.models import Book
from app.serializers import BookSerializer, BookOutputSerializer
    
class BookAPI(CreateAPI, ListAPI):
    input_model = BookSerializer
    output_model = BookOutputSerializer
    pagination = Pagination
    search_fields = ['name', 'author']
    filter_fields = ['name', 'author']
    sort_fields = ['name', 'pages_count']

    async def objects(self, request: Request, **kwargs):
        return await Book.find()
```


### API - Retrieve a Book

Now we are going to retrieve a book on `GET` request, we need to:

1. Inherit from `RetrieveAPI`:
    ```python
    from panther.generics import RetrieveAPI
    
    
    class SingleBookAPI(RetrieveAPI):
        ...
    ```

2. define `object` method, so the `RetrieveAPI` knows to return which book

    ```python
    from panther.generics import RetrieveAPI
    from panther.request import Request
    from app.models import Book
    
    
    class SingleBookAPI(RetrieveAPI):
        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

3. Add it in `app/urls.py`:

    ```python  
    from app.apis import BookAPI, SingleBookAPI
    
    
    urls = {
        'book/': BookAPI,
        'book/<book_id>/': SingleBookAPI,
    }
    ```

   > You should write the [Path Variable](https://pantherpy.github.io/urls/#path-variables-are-handled-like-below) in `<` and `>`


### API - Update a Book

1. Inherit from `UpdateAPI`

    ```python
    from panther.generics import RetrieveAPI, UpdateAPI
    from panther.request import Request
    from app.models import Book
    
    
    class SingleBookAPI(RetrieveAPI, UpdateAPI):
        ...
        
        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

2. Add `input_model` so the `UpdateAPI` knows how to validate the `request.data`
> We use the same serializer as CreateAPI serializer we defined above

    ```python
    from panther.generics import RetrieveAPI, UpdateAPI
    from panther.request import Request
    from app.models import Book
    from app.serializers import BookSerializer
    
    
    class SingleBookAPI(RetrieveAPI, UpdateAPI):
        input_model = BookSerializer
    
        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

### API - Delete a Book

1. Inherit from `DeleteAPI`

    ```python
    from panther.generics import RetrieveAPI, UpdateAPI, DeleteAPI
    from panther.request import Request
    from app.models import Book
    from app.serializers import BookSerializer
    
    
    class SingleBookAPI(RetrieveAPI, UpdateAPI, DeleteAPI):
        input_model = BookSerializer
   
        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

2. It requires `object` method which we defined before, so it's done.
