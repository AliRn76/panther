We assume you have successfully set up your project following the [Introduction](https://pantherpy.github.io/#installation) guide.

In this guide, we will create a `CRUD` (`Create`, `Retrieve`, `Update`, and `Delete`) API for managing `Book` entities.

---

## Project Structure
The final structure of your project will be as follows:
```
.
├── app
│     ├── apis.py
│     ├── models.py
│     ├── serializers.py
│     └── urls.py
└── core
      ├── configs.py
      └── urls.py
```

## Configuring the Database

!!! question "How does the database work in Panther?"
    Refer to [[this page](/database/)] to learn about supported databases and their functionality.

Configure the `DATABASE` settings in `core/configs.py`. In this guide, we will use `PantherDB`.

> [PantherDB](https://github.com/PantherPy/PantherDB/#readme) is a simple, file-based, document-oriented database.

```python title="configs.py"
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
    }
}
```

---

## Defining the Model

!!! question "How do models work in Panther?"
    Refer to [[this page](/model/)] to learn more about defining models and how they function.

Create a model named `Book` in `app/models.py`:

```python title="models.py" linenums="1"
from panther.db import Model


class Book(Model):
    name: str
    author: str
    pages_count: int
```  

---

## Defining URLs

!!! question "How do URLs work in Panther?"
    Refer to [[this page](/urls/)] to learn more about URL definitions.

The base `urls` configuration should include all application URLs.

```python title="core/urls.py" linenums="1"
from app.urls import urls as app_urls


urls = {
    '/': app_urls,
}
```  
In `app/urls.py`, define the `Book` API URLs:

=== "Function-Base"

    ```python title="app/urls.py" linenums="1"
    from app.apis import book_api, single_book_api
    
    urls = {
        'book/': book_api,
        'book/<book_id>/': single_book_api,
    }
    ```

=== "Class-Base API/ Generic API (Beta)"

    ```python title="app/urls.py" linenums="1"
    from app.apis import BookAPI, SingleBookAPI
    
    urls = {
        'book/': BookAPI,
        'book/<book_id>/': SingleBookAPI,
    }
    ```

---

## Defining the Serializer

!!! question "How do serializers work in Panther?"
    Refer to [[this page](/serializer/)] to learn more about available serializers.

Serializers transform data between the application and API requests.

=== "Function-Base/ Class-Base API"
    The serializer can be inherited from `ModelSerializer` or `pydantic.BaseModel`

    ```python title="serializers.py" linenums="1"
    from panther.serializer import ModelSerializer
    
    from app.models import Book
    
    class BookSerializer(ModelSerializer):
        class Config:
            model = Book
            fields = ['name', 'author', 'pages_count']
    ```
    or

    ```python title="serializers.py" linenums="1"
    import pydantic
    
    from app.models import Book
    
    class BookSerializer(pydantic.BaseModel):
        name: str
        author: str
        pages_count: int
    ```

=== "Generic API (Beta)"
    The serializer should be inherited from `ModelSerializer` to be used in `GenericAPI`.

    ```python title="serializers.py" linenums="1"
    from panther.serializer import ModelSerializer
    
    from app.models import Book
    
    class BookSerializer(ModelSerializer):
        class Config:
            model = Book
            fields = ['name', 'author', 'pages_count']
    ```


### APIs
!!! question "How do APIs work in Panther?"
    Refer to [[this page](/api/)] to learn more about API types and their usage.

#### Create

=== "Function-Base API"

    ```python title="apis.py" linenums="1"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response

    from app.serializers import BookSerializer
    from app.models import Book
    
    
    @API(input_model=BookSerializer, methods=['POST'])
    async def book_api(request: Request):
        body: BookSerializer = request.validated_data
        book: Book = await Book.insert_one(
            name=body.name,
            author=body.author,
            pages_count=body.pages_count,
        )
        return Response(data=book, status_code=status.HTTP_201_CREATED)
    ```

=== "Class-Base API"

    ```python title="apis.py" linenums="1"
    from panther import status
    from panther.app import GenericAPI
    from panther.request import Request
    from panther.response import Response
    
    from app.serializers import BookSerializer
    from app.models import Book
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
    
        async def post(self, request: Request):
            body: BookSerializer = request.validated_data
            book = await Book.insert_one(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            return Response(data=book, status_code=status.HTTP_201_CREATED)
    ```

=== "Generic API (Beta)"

    ```python title="apis.py" linenums="1"
    from panther.app import CreateAPI

    from app.serializers import BookSerializer
    
    
    class BookAPI(CreateAPI):
        input_model = BookSerializer
    ```

#### List

=== "Function-Base API"

    ```python title="apis.py" linenums="1"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response

    from app.serializers import BookSerializer
    from app.models import Book
    
    
    @API(input_model=BookSerializer, methods=['POST', 'GET'])
    async def book_api(request: Request):
        if request.method == 'POST':
            body: BookSerializer = request.validated_data
            book: Book = await Book.insert_one(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            return Response(data=book, status_code=status.HTTP_201_CREATED) 
        else:  # GET
            books = await Book.find()
            return Response(data=books, status_code=status.HTTP_200_OK)
    ```

=== "Class-Base API"

    ```python title="apis.py" linenums="1"
    from panther import status
    from panther.app import GenericAPI
    from panther.request import Request
    from panther.response import Response
    
    from app.serializers import BookSerializer
    from app.models import Book
    
    
    class BookAPI(GenericAPI):
        input_model = BookSerializer
    
        async def post(self, request: Request):
            body: BookSerializer = request.validated_data
            book = await Book.insert_one(
                name=body.name,
                author=body.author,
                pages_count=body.pages_count,
            )
            return Response(data=book, status_code=status.HTTP_201_CREATED)

        async def get(self):
            books = await Book.find()
            return Response(data=books, status_code=status.HTTP_200_OK)
    ```

=== "Generic API (Beta)"

    ```python title="apis.py" linenums="1"
    from panther.generics import CreateAPI, ListAPI
    from panther.pagination import Pagination
    from panther.request import Request
    
    from app.models import Book
    from app.serializers import BookSerializer
        
    class BookAPI(CreateAPI, ListAPI):
        input_model = BookSerializer
        pagination = Pagination  #(1)!
        search_fields = ['name', 'author']  #(2)!
        filter_fields = ['name', 'author']  #(3)!
        sort_fields = ['name', 'pages_count']  #(4)!
    
        async def cursor(self, request: Request, **kwargs):
            return await Book.find()
    ```

    1. `Pagination` class will look for the `limit` and `skip` in the `query params` and paginate your response and then return it on its own response template.
    Check out: [Pagination](/pagination/) for more detail.
    2. The query will be changed and looking for the value of the `search` query param in these fields,
    e.g. query param is the `?search=TheLittlePrince`, we will looking for the Book with `name` or `author` of `TheLittlePrince`.
    Check out: [Search Fields](/api/#search_fields/) for more detail.
    3. It will look for each value of the `filter_fields` in the `query params` and query on them, 
    e.g. `?name=Something&author=Ali`, it will looks for Book that its `author` is `Ali` and its `name` is `Something`.
    Check out: [Filter Fields](/api/#filter_fields/) for more detail.
    4. The query will be sortalbe with the fields which is in `sort_fields`.
    Check out: [Sort Fields](/api/#sort_fields/) for more detail.

#### Retrieve

=== "Function-Base API"

    ```python title="apis.py" linenums="23"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response

    from app.models import Book
    
   
    @API(methods=['GET'])
    async def single_book_api(request: Request, book_id: int):
        if book := await Book.find_one(id=book_id):
            return Response(data=book, status_code=status.HTTP_200_OK)
        return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)
    ```

=== "Class-Base API"

    ```python title="apis.py" linenums="25"
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    from app.models import Book
    
   
    class SingleBookAPI(GenericAPI):
        async def get(self, book_id: int):
            if book := await Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)
    ```

=== "Generic API (Beta)"

    ```python title="apis.py" linenums="17"
    from panther.generics import RetrieveAPI
    from panther.request import Request

    from app.models import Book
    
    
    class SingleBookAPI(RetrieveAPI):
        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

#### Update

=== "Function-Base API"

    ```python title="apis.py" linenums="23"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response

    from app.models import Book
    from app.serializers import BookSerializer 
    
   
    @API(input_model=BookSerializer, methods=['GET', 'PUT'])
    async def single_book_api(request: Request, book_id: int):
        if request.method == 'GET':
            if book := await Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)
        
        else:  # 'PUT'            
            is_updated = await Book.update_one({'id': book_id}, request.validated_data.model_dump())
            data = {'is_updated': is_updated}
            return Response(data=data, status_code=status.HTTP_200_OK)
    ```

=== "Class-Base API"

    ```python title="apis.py" linenums="25"
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    from app.models import Book
    
   
    class SingleBookAPI(GenericAPI):
        async def get(self, book_id: int):
            if book := await Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)

        async def put(self, request: Request, book_id: int):
            is_updated = await Book.update_one({'id': book_id}, request.validated_data.model_dump())
            data = {'is_updated': is_updated}
            return Response(data=data, status_code=status.HTTP_200_OK)
    ```

=== "Generic API (Beta)"

    ```python title="apis.py" linenums="17"
    from panther.generics import RetrieveAPI
    from panther.request import Request

    from app.models import Book
    from app.serializers import BookSerializer
    
    
    class SingleBookAPI(RetrieveAPI, UpdateAPI):
        input_model = BookSerializer

        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```


#### Delete

=== "Function-Base API"

    ```python title="apis.py" linenums="23"
    from panther import status
    from panther.app import API
    from panther.request import Request
    from panther.response import Response

    from app.models import Book
    from app.serializers import BookSerializer 
    
   
    @API(input_model=BookSerializer, methods=['GET', 'PUT', 'DELETE'])
    async def single_book_api(request: Request, book_id: int):
        if request.method == 'GET':
            if book := await Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'PUT':       
            is_updated = await Book.update_one({'id': book_id}, request.validated_data.model_dump())
            data = {'is_updated': is_updated}
            return Response(data=data, status_code=status.HTTP_200_OK)
        
        else:  # 'DELETE'
            await Book.delete_one(id=book_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    ```

=== "Class-Base API"

    ```python title="apis.py" linenums="25"
    from panther import status
    from panther.app import GenericAPI
    from panther.response import Response
    
    from app.models import Book
    
   
    class SingleBookAPI(GenericAPI):
        async def get(self, book_id: int):
            if book := await Book.find_one(id=book_id):
                return Response(data=book, status_code=status.HTTP_200_OK)
            return Response(data={'detail': 'Book not found'}, status_code=status.HTTP_400_BAD_REQUEST)

        async def put(self, request: Request, book_id: int):
            is_updated = await Book.update_one({'id': book_id}, request.validated_data.model_dump())
            data = {'is_updated': is_updated}
            return Response(data=data, status_code=status.HTTP_200_OK)

        async def delete(self, book_id: int):
            await Book.delete_one(id=book_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    ```

=== "Generic API (Beta)"

    ```python title="apis.py" linenums="17"
    from panther.generics import RetrieveAPI
    from panther.request import Request

    from app.models import Book
    from app.serializers import BookSerializer
    
    
    class SingleBookAPI(RetrieveAPI, UpdateAPI, DeleteAPI):
        input_model = BookSerializer

        async def object(self, request: Request, **kwargs):
            return await Book.find_one_or_raise(id=kwargs['book_id'])
    ```

With this, you now have a complete CRUD API implementation for the `Book` entity.
