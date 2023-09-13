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

### Add Database Middleware

Add one database middleware in `core/configs.py` `MIDDLEWARES`, we are going to add `pantherdb`
> [PantherDB](https://github.com/PantherPy/PantherDB/#readme) is a Simple, FileBase and Document Oriented database:

```python
...

MIDDLEWARES = [
    ('panther.middlewares.db.Middleware', {'url': f'pantherdb://{BASE_DIR}/{DB_NAME}.pdb'}),
]
```

## APIs
### API - Create a Book

Now we are going to create a book on `post` request, We need to:

1. Declare `post` method in `BookAPI`:
    ```python
    from panther.app import GenericAPI
    
    
    class BookAPI(GenericAPI):
        
        def post(self):
            ...
    ```


2. Declare `request: Request` in `BookAPI.post()` function:
    ```python
    from panther.app import GenericAPI
    from panther.request import Request
    
    
    class BookAPI(GenericAPI):
        
        def post(self, request: Request):
            ...
    ```

3. Create serializer in `app/serializers.py`, we used `pydantic` for the `validation` of `request.data` :
    ```python
    from pydantic import BaseModel
    
    
    class BookSerializer(BaseModel):
        name: str
        author: str
        pages_count: int
    ```

4. Pass the created serializer to our `BookAPI` as `input_model` so the incoming data will be validated and cleaned automatically:

    ```python
    from panther.app import GenericAPI
    from panther.request import Request
    
    from app.serializers import BookSerializer
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
   
        def post(self, request: Request):
            ...
    
    ```
   Now we have access to `request.data`, We are going to use it like the below for ease of use, so the auto-suggest helps us in development:

    ```python
    from panther.app import GenericAPI
    from panther.request import Request
    
    from app.serializers import BookSerializer
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
   
        def post(self, request: Request):
            body: BookSerializer = request.validated_data
            ...
    ```

4. Now we have access to the validated data, and we can create our first book:

    ```python
    from panther.app import GenericAPI
    from panther.request import Request
    
    from app.serializers import BookSerializer
    from app.models import Book
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
    
        def post(self, request: Request):
            body: BookSerializer = request.validated_data
            Book.insert_one(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            ...
    ```

5. And finally we return `201 Created` status_code as response of `post`:
    ```python
    from panther import status
    from panther.app import GenericAPI
    from panther.request import Request
    from panther.response import Response
    
    from app.serializers import BookSerializer
    from app.models import Book
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
    
        def post(self, request: Request):
            body: BookSerializer = request.validated_data
            book = Book.insert_one(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            return Response(data=book, status_code=status.HTTP_201_CREATED)

    ```

> The response.data can be `Instance of Models`, `dict`, `str`, `tuple`, `list`, `str` or `None`

> Panther will return `None` if you don't return anything as response.


### API - List of Books

We just need to add another method for `GET` method and return the lists of books:

```python
from panther import status
from panther.app import GenericAPI
from panther.request import Request
from panther.response import Response

from app.serializers import BookSerializer
from app.models import Book


class BookAPI(GenericAPI):
    input_model = BookSerializer

    def post(self, request: Request):
        ...
    
    def get(self):
        books: list[Book] = Book.find()
        return Response(data=books, status_code=status.HTTP_200_OK)
   
```

> Panther validate input with `input_model`, only in `POST`, `PUT`, `PATCH` methods.

### Filter Response Fields

Assume we don't want to return field `author` in response:


1. Create new serializer in `app/serializers.py`:

    ```python
    from pydantic import BaseModel
    
    
    class BookOutputSerializer(BaseModel):
        name: str
        pages_count: int
    ```

2. Add the `BookOutputSerializer` as `output_model` to your `class`

    ```python
    from panther import status
    from panther.app import GenericAPI
    from panther.request import Request
    from panther.response import Response
    
    from app.serializers import BookSerializer, BookOutputSerializer
    from app.models import Book
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
        output_model = BookOutputSerializer
    
        def post(self, request: Request):
            ...
    
        def get(self):
            books: list[Book] = Book.find()
            return Response(data=books, status_code=status.HTTP_200_OK)
    ```

> Panther use the `output_model`, in all methods.


### Cache The Response

For caching the response, we should add `cache=True` in `API()`.
And it will return the cached response every time till `cache_exp_time`

For setting a custom expiration time for API we need to add `cache_exp_time` to `API()`:

```python
from datetime import timedelta

from panther import status
from panther.app import GenericAPI
from panther.request import Request
from panther.response import Response

from app.serializers import BookSerializer, BookOutputSerializer
from app.models import Book


class BookAPI(GenericAPI):
    input_model = BookSerializer
    output_model = BookOutputSerializer
    cache = True
    cache_exp_time = timedelta(seconds=10)

    def post(self, request: Request):
        ...

    def get(self):
        books: list[Book] = Book.find()
        return Response(data=books, status_code=status.HTTP_200_OK)
    
```

> Panther is going to use the `DEFAULT_CACHE_EXP` from `core/configs.py` if `cache_exp_time` has not been set.


### Throttle The Request

For setting rate limit for requests, we can add [throttling](https://pantherpy.github.io/throttling/) to `BookAPI`, it should be the instance of `panther.throttling.Throttling`,
something like below _(in the below example user can't request more than 10 times in a minutes)_:

```python
from datetime import timedelta

from panther import status
from panther.app import GenericAPI
from panther.request import Request
from panther.response import Response
from panther.throttling import Throttling

from app.serializers import BookSerializer, BookOutputSerializer
from app.models import Book


class BookAPI(GenericAPI):
    input_model = BookSerializer
    output_model = BookOutputSerializer
    cache = True
    cache_exp_time = timedelta(seconds=10)
    throttling = Throttling(rate=10, duration=timedelta(minutes=1))

    def post(self, request: Request):
        ...

    def get(self):
        books: list[Book] = Book.find()
        return Response(data=books, status_code=status.HTTP_200_OK)
   
```


### API - Retrieve a Book

For `retrieve`, `update` and `delete` API, we are going to

1. Create another class named `SingleBookAPI` in `app/apis.py`:

    ```python
    from panther.app import GenericAPI

       
    class SingleBookAPI(GenericAPI):
        ...
    ```

2. Add it in `app/urls.py`:

    ```python  
    from app.apis import BookAPI, SingleBookAPI
    
    
    urls = {
        'book/': BookAPI,
        'book/<book_id>/': SingleBookAPI,
    }
    ```

   > You should write the [Path Variable](https://pantherpy.github.io/urls/#path-variables-are-handled-like-below) in `<` and `>`

   > You should have the parameter with the same name of `path variable` in you `api` with normal `type hints`

   > Panther will convert type of the `path variable` to your parameter type, then pass it

3. Complete the api:

    ```python
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    from app.models import Book
    
   
    class SingleBookAPI(GenericAPI):
        
        def get(self, book_id: int):
            if book := Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            else:
                return Response(status_code=status.HTTP_404_NOT_FOUND)
    ```

### API - Update a Book

- We can update in several ways:
    1. Update a document

        ```python
        from panther import status
        from panther.app import GenericAPI
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       
       
        class SingleBookAPI(GenericAPI):
            input_model = BookSerializer
       
            def get(self, book_id: int):
                ...
            
            def put(self, request: Request, book_id: int):
                body: BookSerializer = request.validated_data
       
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
        from panther.app import GenericAPI
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       

        class SingleBookAPI(GenericAPI):
            input_model = BookSerializer
       
            def get(self, book_id: int):
                ...
            
            def put(self, request: Request, book_id: int):
                is_updated: bool = Book.update_one({'id': book_id}, request.validated_data.model_dump())
                data = {'is_updated': is_updated}
                return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
        ```

    3. Update with `update_many` query

        ```python
        from panther import status
        from panther.app import GenericAPI
        from panther.request import Request
        from panther.response import Response
        
        from app.models import Book
        from app.serializers import BookSerializer
       
        
        class SingleBookAPI(GenericAPI):
            input_model = BookSerializer
       
            def get(self, book_id: int):
                ...
            
            def put(self, request: Request, book_id: int):
                updated_count: int = Book.update_many({'id': book_id}, request.validated_data.model_dump())
                data = {'updated_count': updated_count}
                return Response(data=data, status_code=status.HTTP_202_ACCEPTED)
        ```
       
    > You can handle the PATCH the same way as PUT

### API - Delete a Book

- We can delete in several ways too:
    1. Delete a document

        ```python
            from panther import status
            from panther.app import GenericAPI
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
            class SingleBookAPI(GenericAPI):
                input_model = BookSerializer
       
                def get(self, book_id: int):
                    ...
            
                def put(self, request: Request, book_id: int):
                    ...
                  
                def delete(self, book_id: int):
                    is_deleted: bool = Book.delete_one(id=book_id)
                    if is_deleted:
                        return Response(status_code=status.HTTP_204_NO_CONTENT)
                    else:
                        return Response(status_code=status.HTTP_400_BAD_REQUEST)
        ```
    2. Delete with `delete_one` query

        ```python
            from panther import status
            from panther.app import GenericAPI
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
           
            class SingleBookAPI(GenericAPI):
                input_model = BookSerializer
       
                def get(self, book_id: int):
                    ...
            
                def put(self, request: Request, book_id: int):
                    ...
                  
                def delete(self, book_id: int):
                    is_deleted: bool = Book.delete_one(id=book_id)
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
        ```
       
    3. Delete with `delete_many` query

        ```python
            from panther import status
            from panther.app import GenericAPI
            from panther.request import Request
            from panther.response import Response
            
            from app.models import Book
            
           
            class SingleBookAPI(GenericAPI):
                input_model = BookSerializer
       
                def get(self, book_id: int):
                    ...
            
                def put(self, request: Request, book_id: int):
                    ...
                  
                def delete(self, book_id: int):
                    deleted_count: int = Book.delete_many(id=book_id)
                    return Response(status_code=status.HTTP_204_NO_CONTENT)
        ```