We assume you could run the project with [Introduction](https://pantherpy.github.io/#installation)

Now let's write custom API `Create`, `Retrieve`, `Update` and `Delete` a `Book`:

### Create Book Model

We should create the `book` model in `app/models.py`, like below:


```python  
from panther.db import Model


class Book(Model):
    name: str
    author: str
    pages_count: int
```  

### Create API Function

We should create our `APIs` in `app/apis.py`, like below:

```python  
from panther.app import API


@API()
async def book_api():
    ... 
```  

We going to complete it later ...

### Add API to URLs

We should add our new api to `app/urls.py`, like below:

```python  
from app.apis import book_api


urls = {
    'book/': book_api,
}
```

and we assume the `urls` in `core/urls.py` pointed to `app/urls.py` like below:

```python  
from app.urls import urls as app_urls


urls = {
    '/': app_urls,
}
```

### Add Database Middleware

You should add one database middleware to your `core/configs.py` middlewares, we going to add `pantherdb` (it's file base & required nothing ...), like below:

```python
...

MIDDLEWARES = [
    ('panther.middlewares.db.Middleware', {'url': f'pantherdb://{BASE_DIR}/{DB_NAME}.pdb'}),
]
```


### API - Create a Book

Now we are going to create a book on `post` request, then we need to:
1.  Pass the `request: Request` to our `book_api` , like below:

```python
from panther.app import API
from panther.request import Request


@API()
async def book_api(request: Request):
    ...

```

2. Create serializer for it in `app/serializers.py`, we used `pydantic` for the `validation` of `request.data` :
```python
from pydantic import BaseModel


class BookSerializer(BaseModel):
    name: str
    author: str
    pages_count: int
```

3. Pass the created serializer to our `book_api` as `input_model` so the incoming data will be validate and cleaned automatically, like below:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer


@API(input_model=BookSerializer)
async def book_api(request: Request):
    ...

```

Now we can access the `request.data`, and for our pleasure, we are going to use it like below, so the IDE auto-suggest help us in development:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer


@API(input_model=BookSerializer)
async def book_api(request: Request):
    body: BookSerializer = request.data
    ...
```

4. Now we have access to the validated data, and we can create our first book, like below:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request):
    body: BookSerializer = request.data

    Book.create(
        name=body.name,
        author=body.author,
        pages_count=body.pages_count,
    )
    ...
```

5. But we only want this happen in `post` requests, so we add this `condition` to it:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request):
    if request.method == 'POST':
        body: BookSerializer = request.data

        Book.create(
            name=body.name,
            author=body.author,
            pages_count=body.pages_count,
        )
        ...
```

6. And finally we return `201 Created` status_code as response of `post` and `501 Not Implemented` for other methods:
```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request):
    if request.method == 'POST':
        body: BookSerializer = request.data

        book = Book.create(
            name=body.name,
            author=body.author,
            pages_count=body.pages_count,
        )
        return Response(data=book, status_code=status.HTTP_201_CREATED)

    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
```

> The data in response can be `Instance of Models`, `dict`, `str`, `tuple`, `list`, `str` or `None`

> Panther will return `None` if you don't return anything as response.


### API - List of Books

We just need to add another condition on `GET` methods and return the lists of books, like below:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request):
    if request.method == 'POST':
        body: BookSerializer = request.data

        book = Book.create(
            name=body.name,
            author=body.author,
            pages_count=body.pages_count,
        )
        return Response(data=book, status_code=status.HTTP_201_CREATED)

    elif request.method == 'GET':
        books = Book.find()
        return Response(data=books, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
```

### API - Retrieve a Book

For `retrieve`, `update` and `delete` API, we are going to

1. Create another api named `single_book_api` in `app/apis.py`, like below:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request): ...

@API()
async def single_book_api(request: Request):
    ...
```

2. Add it to `app/urls.py`:

```python  
from app.apis import book_api, single_book_api


urls = {
    'book/': book_api,
    'book/<book_id>/': single_book_api,
}
```
> You should write the `path variable` in `<` and `>`

> You should have the parameter with the same name of `path variable` in you `api` with normal `type hints`

> Panther will convert type of the `path variable` to your parameter type, then pass it


3. Complete the api:

```python
from panther.app import API
from panther.request import Request

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request, book_id: int): ...

@API()
async def single_book_api(request: Request, book_id: int):
    if request.method == 'GET':
        book = Book.find_one(id=book_id)
        return Response(data=book, status_code=status.HTTP_200_OK)
```

### API - Update a Book

### API - Delete a Book