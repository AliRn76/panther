Let's write custom API that returns `current time` of your system:


1. Create `time_api()` in `app/apis.py` 

    ```python
    from datetime import datetime
    from panther import status
    from panther.app import API
    from panther.response import Response
    
   
    @API()
    async def time_api():
        return Response(data=datetime.now(), status_code=status.HTTP_202_ACCEPTED)
    ```
   
2. Add `time` url in `app/urls.py` that points to `time_api()`
    
    ```python
   ...
   from app.apis import time_api
   
   
    urls = {
        '': hello_world,
        'info/': info,
        'time/': time_api,
    }
    ```

Now you can see the current time in your browser:

[http://127.0.0.1:8000/time/](http://127.0.0.1:8000/time/)