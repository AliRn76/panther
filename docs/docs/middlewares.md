> <b>Variable:</b> `MIDDLEWARES` 
> 
> <b>Type:</b> `list` 
> 
> <b>Default:</b> `[]`


## Structure of middlewares
`MIDDLEWARES` itself is a `list` of `tuples` which each `tuple` is like below:

(`Dotted Address of The Middleware Class`, `kwargs as dict`)


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

  - Then you can write your custom `before()` and `after()` methods

  - The `methods` should be `async`
  - `before()` should have `request` parameter
  - `after()` should have `response` parameter
  - overwriting the `before()` and `after()` are optional
  - The `methods` can get `kwargs` from their `__init__`

### Custom HTTP Middleware Example
- **core/middlewares.py**
    ```python
    from panther.middlewares.base import HTTPMiddleware
    from panther.request import Request
    from panther.response import Response


    class CustomMiddleware(HTTPMiddleware):

        def __init__(self, something):
            self.something = something

        async def before(self, request: Request) -> Request:
            print('Before Endpoint', self.something)
            return request

        async def after(self, response: Response) -> Response:
            print('After Endpoint', self.something)
            return response
    ```

- **core/configs.py**
    ```python
    MIDDLEWARES = [
          ('core.middlewares.CustomMiddleware', {'something': 'hello-world'}),
    ]
    ```
  
### Custom HTTP + Websocket Middleware Example
- **core/middlewares.py**
    ```python
    from panther.middlewares.base import BaseMiddleware
    from panther.request import Request
    from panther.response import Response
    from panther.websocket import GenericWebsocket 


    class SayHiMiddleware(BaseMiddleware):

        def __init__(self, name):
            self.name = name

        async def before(self, request: Request | GenericWebsocket) -> Request | GenericWebsocket:
            print('Hello ', self.name)
            return request

        async def after(self, response: Response | GenericWebsocket) -> Response | GenericWebsocket:
            print('Goodbye ', self.name)
            return response
    ```

- **core/configs.py**
    ```python
    MIDDLEWARES = [
          ('core.middlewares.SayHiMiddleware', {'name': 'Ali Rn'}),
    ]
    ```