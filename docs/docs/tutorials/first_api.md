Let's write custom API that returns current time of your system:

1. add an url named `time` to your app/urls.py that points to `time_api` function
    
    ```python
    urls = {
        '': hello_world,
        'info/': info,
        'time/': time_api,
    }
    ```

2. create `time_api` function in `app.apis.py` 

    ```python
    from datetime import datetime
    from panther.app import API
    from panther.response import Response
    from panther import status
    
    @API()
    async def time_api():
        return Response(data=datetime.now(), status_code=status.HTTP_202_ACCEPTED)
    ```
   
Now you can see the current time in your browser:

[http://127.0.0.1:8000/time/](http://127.0.0.1:8000/time/)