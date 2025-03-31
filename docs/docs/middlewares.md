> <b>Variable:</b> `MIDDLEWARES` 
> 
> <b>Type:</b> `list` 
> 
> <b>Default:</b> `[]`


## Definition
### Global

`MIDDLEWARES` is a `list` of middlewares address or their class itself, like below:

```python
class Middleware:
    pass

MIDDLEWARES = [
    'core.middlewares.MyMiddleware', 
    Middleware,  # Mostly used in single-file projects
]
```

### Per API

`Middlewares` can be assigned to `APIs` directly too,


```python
from panther.app import API, GenericAPI

class Middleware:
    pass

# Class-Based
class MyAPI(GenericAPI):
    middlewares = [Middleware]

# Function-Based
@API(middlewares=[Middleware])
def my_api():
    pass
```

### Middlewares Priority

1. (`Global Middlewares`)`.before()`
2. (`PerAPI Middlewares`)`.before()`
3. (`PerAPI Middlewares`)`.after()`
4. (`Global Middlewares`)`.after()`


## Custom Middleware
### Middleware Types
  We have 3 type of Middlewares, make sure that you are inheriting from the correct one:

  - `Base Middleware`: which is used for both `websocket` and `http` requests 

  - `HTTP Middleware`: which is only used for `http` requests

  - `Websocket Middleware`: which is only used for `websocket` requests

### Write Custom Middleware
  - Write a `class` and inherit from one of the classes below
    ```python
    # For HTTP Requests
    from panther.middlewares.base import HTTPMiddleware
    
    # For Websocket Requests
    from panther.middlewares.base import WebsocketMiddleware
    
    # For Both HTTP and Websocket Requests
    from panther.middlewares.base import BaseMiddleware
    ```

  - Then you can write your own `before()` and `after()` methods
  - The `methods` should be `async`
  - `before()` should have `request` parameter
  - `after()` should have `response` parameter
  - overwriting the `before()` and `after()` are optional

### HTTP Middleware Example

```python
from panther.middlewares.base import HTTPMiddleware
from panther.request import Request
from panther.response import Response


class CustomMiddleware(HTTPMiddleware):
    async def before(self, request: Request) -> Request:
        print('Before Endpoint')
        return request

    async def after(self, response: Response) -> Response:
        print('After Endpoint')
        return response
```

### (HTTP + Websocket) Middleware Example

```python
from datetime import datetime
from panther.middlewares.base import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.websocket import GenericWebsocket 


class TimerMiddleware(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket) -> Request | GenericWebsocket:
        self.start_time = datetime.now()
        return request

    async def after(self, response: Response | GenericWebsocket) -> Response | GenericWebsocket:
        result = datetime.now() - self.start_time
        print(f'Request takes {result.total_seconds()} seconds')
        return response
```
