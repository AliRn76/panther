Now we are going to create a new API which uses our default database(`PantherDB`) and creating a `Book`

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
    from app.apis import time_api, book_api
    
    
    urls = {
        '': hello_world,
        'info/': info,
        'time/': time_api,
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

4. Now we should use the `Panther ODM` to create a book, it's based on mongo queries, for creation we use `insert_one` like this:

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

In next step we are going to explain more about `Panther ODM`