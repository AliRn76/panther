We assume you could run the project with [Introduction](https://pantherpy.github.io/#installation)

Now let's write custom API `Create`, `Retrieve`, `Update` and `Delete` for a `Book`:

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

### Create API Function

Create the `book_api()` in `app/apis.py`:

```python  
from panther.app import API


@API()
async def book_api():
    ... 
```  

> We are going to complete it later ...

### Update URLs

Add the `book_api` in `app/urls.py`:

```python  
from app.apis import book_api


urls = {
    'book/': book_api,
}
```

We assume that the `urls` in `core/urls.py` pointing to `app/urls.py`, like below:

```python  
from app.urls import urls as app_urls


urls = {
    '/': app_urls,
}
```

### Add Database Middleware

Add one database middleware in `core/configs.py` `MIDDLEWARES`, we are going to add `pantherdb`
> [PantherDB](https://github.com/AliRn76/PantherDB/#readme) is a Simple, FileBase and Document Oriented database:

```python
...

MIDDLEWARES = [
    ('panther.middlewares.db.Middleware', {'url': f'pantherdb://{BASE_DIR}/{DB_NAME}.pdb'}),
]
```

## APIs
### API - Create a Book

Now we are going to create a book on `post` request, We need to:

1. Declare `request: Request` in `book_api` function:
    ```python
    from panther.app import API
    from panther.request import Request
    
    
    @API()
    async def book_api(request: Request):
        ...
    
    ```

2. Create serializer in `app/serializers.py`, we used `pydantic` for the `validation` of `request.data` :
    ```python
    from pydantic import BaseModel
    
    
    class BookSerializer(BaseModel):
        name: str
        author: str
        pages_count: int
    ```

3. Pass the created serializer to our `book_api` as `input_model` so the incoming data will be validated and cleaned automatically:

    ```python
    from panther.app import API
    from panther.request import Request
    
    from app.serializers import BookSerializer
    
    
    @API(input_model=BookSerializer)
    async def book_api(request: Request):
        ...
    
    ```
   Now we have access to `request.data`, We are going to use it like the below for ease of use, so the auto-suggest helps us in development:

    ```python
    from panther.app import API
    from panther.request import Request
    
    from app.serializers import BookSerializer
    
    
    @API(input_model=BookSerializer)
    async def book_api(request: Request):
        body: BookSerializer = request.data
        ...
    ```

4. Now we have access to the validated data, and we can create our first book:

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

5. But we only want this happens in `post` requests, so we add this `condition`:

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
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response
    
    from app.serializers import BookSerializer
    from app.models import Book
    
    
    @API(input_model=BookSerializer)
    async def book_api(request: Request):
        if request.method == 'POST':
            body: BookSerializer = request.data
    
            book: Book = Book.create(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            return Response(data=book, status_code=status.HTTP_201_CREATED)
    
        return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
    ```

> The response.data can be `Instance of Models`, `dict`, `str`, `tuple`, `list`, `str` or `None`

> Panther will return `None` if you don't return anything as response.


### API - List of Books

We just need to add another condition on `GET` methods and return the lists of books:

```python
from panther import status
from panther.app import API
from panther.request import Request
from panther.response import Response

from app.serializers import BookSerializer
from app.models import Book


@API(input_model=BookSerializer)
async def book_api(request: Request):
    if request.method == 'POST':
        ...

    elif request.method == 'GET':
        books: list[Book] = Book.find()
        return Response(data=books, status_code=status.HTTP_200_OK)

    return Response(status_code=status.HTTP_501_NOT_IMPLEMENTED)
```

### API - Retrieve a Book

For `retrieve`, `update` and `delete` API, we are going to

1. Create another api named `single_book_api` in `app/apis.py`:

    ```python
    from panther.app import API
    from panther.request import Request
    
    
    @API()
    async def single_book_api(request: Request):
        ...
    ```

2. Add it in `app/urls.py`:

    ```python  
    from app.apis import book_api, single_book_api
    
    
    urls = {
        'book/': book_api,
        'book/<book_id>/': single_book_api,
    }
    ```

   > You should write the [Path Variable](https://pantherpy.github.io/urls/#path-variables-are-handled-like-below) in `<` and `>`

   > You should have the parameter with the same name of `path variable` in you `api` with normal `type hints`

   > Panther will convert type of the `path variable` to your parameter type, then pass it

3. Complete the api:

    ```python
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response
    
    from app.models import Book
    
   
    @API()
    async def single_book_api(request: Request, book_id: int):
        if request.method == 'GET':
            book: Book = Book.find_one(id=book_id)
            return Response(data=book, status_code=status.HTTP_200_OK)
    ```

### API - Update a Book

- We can update in several ways:
    1. Update a document

        ```python
        from panther import status
        from panther.app import API
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       
       
        @API(input_model=BookSerializer)
        async def single_book_api(request: Request, book_id: int):
            body: BookSerializer = request.data
            if request.method == 'GET':
                ...
            elif request.method == 'PUT':
                book: Book = Book.find_one(id=book_id)
                book.update(
                    name=body.name, 
                    author=body.author, 
                    pages_count=body.pages_count
                    )
                return Response(status_code=status.HTTP_202_ACCEPTED)
        ```

    2. Update with `update_one` query

        ```python
        from panther import status
        from panther.app import API
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       
       
        @API(input_model=BookSerializer)
        async def single_book_api(request: Request, book_id: int):
            if request.method == 'GET':
                ...
            elif request.method == 'PUT':
                is_updated: bool = Book.update_one({'id': book_id}, **request.data)
                data = {'is_updated': is_updated}
                return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
        ```

    3. Update with `update_many` query

        ```python
        from panther import status
        from panther.app import API
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       
        
        @API(input_model=BookSerializer)
        async def single_book_api(request: Request, book_id: int):
            if request.method == 'GET':
                ...
            elif request.method == 'PUT':
                updated_count: int = Book.update_many({'id': book_id}, **request.data)
                data = {'updated_count': updated_count}
                return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
        ```
       
    > You can handle the PATCH the same way as PUT

### API - Delete a Book

- We can delete in several ways too:
    1. Delete a document

        ```python
            from panther import status
            from panther.app import API
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
           
            @API()
            async def single_book_api(request: Request, book_id: int):
                if request.method == 'GET':
                    ...
                elif request.method == 'PUT':
                    ...
                elif request.method == 'DELETE':
                    book: Book = Book.find_one(id=book_id)
                    book.delete()
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
        ```
    2. Delete with `delete_one` query

        ```python
            from panther import status
            from panther.app import API
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
           
            @API()
            async def single_book_api(request: Request, book_id: int):
                if request.method == 'GET':
                    ...
                elif request.method == 'PUT':
                    ...
                elif request.method == 'DELETE':
                    is_deleted: bool = Book.delete_one(id=book_id)
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
        ```
       
    3. Delete with `delete_many` query

        ```python
            from panther import status
            from panther.app import API
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
           
            @API()
            async def single_book_api(request: Request, book_id: int):
                if request.method == 'GET':
                    ...
                elif request.method == 'PUT':
                    ...
                elif request.method == 'DELETE':
                    deleted_count: int = Book.delete_many(id=book_id)
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
        ```