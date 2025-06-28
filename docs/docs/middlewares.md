# Middlewares in Panther

Middlewares allow you to process requests and responses globally or for all or specific APIs. They are useful for tasks such as logging, timing, and other cross-cutting concerns.

---

## Global Middlewares

To apply middlewares globally, define a `MIDDLEWARES` list in your configs. Each item can be either a string (dotted path to the middleware class) or the class itself (useful for single-file applications):

```python
class Middleware(HTTPMiddleware):
    pass

MIDDLEWARES = [
    'core.middlewares.MyMiddleware',  # Import by dotted path
    Middleware,                       # Or directly by class
]
```

---

## Per-API Middlewares

You can assign middlewares to specific APIs, either class-based or function-based:

```python title="apis.py" linenums="1"
from panther.app import API, GenericAPI
from panther.middlewares import HTTPMiddleware

class Middleware(HTTPMiddleware):
    pass

# Class-Based API
class MyAPI(GenericAPI):
    middlewares = [Middleware]

# Function-Based API
@API(middlewares=[Middleware])
def my_api():
    pass
```

---

## Middleware Execution Order

Middlewares are executed in the following order:

1. Global middlewares: `__call__()` (enter)
2. Per-API middlewares: `__call__()` (enter)
3. Per-API middlewares: `dispatch` (return)
4. Global middlewares: `dispatch` (return)

---

## Creating Custom Middlewares

### Types of Middlewares

Panther provides two types of middleware base classes:

- `HTTPMiddleware`: For HTTP requests only
- `WebsocketMiddleware`: For WebSocket connections only

Make sure to inherit from the correct base class:

```python
# For HTTP requests
from panther.middlewares import HTTPMiddleware

# For WebSocket connections
from panther.middlewares import WebsocketMiddleware
```

### Implementing a Middleware

- Create a class inheriting from `HTTPMiddleware` or `WebsocketMiddleware`.
- Implement an asynchronous `__call__` method.
- Always return either `await self.dispatch(...)` or a `Response`/`GenericWebsocket` instance at the end of `__call__()`.

#### Example: HTTP Middleware

```python title="middlewares.py" linenums="1"
from datetime import datetime
from panther.middlewares.base import HTTPMiddleware
from panther.request import Request
from panther.response import Response

class CustomMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request) -> Response:
        start_time = datetime.now()
        response = await self.dispatch(request=request)
        duration = datetime.now() - start_time
        print(f'Request took {duration.total_seconds()} seconds')
        return response
```

#### Example: WebSocket Middleware

```python title="middlewares.py" linenums="1"
from datetime import datetime
from panther.middlewares.base import WebsocketMiddleware
from panther.websocket import GenericWebsocket, Websocket

class TimerMiddleware(WebsocketMiddleware):
    async def __call__(self, connection: Websocket) -> GenericWebsocket:
        start_time = datetime.now()
        response = await self.dispatch(connection=connection)
        duration = datetime.now() - start_time
        print(f'Connection lasted {duration.total_seconds()} seconds')
        return response
```

---

## Built-in Middlewares

Panther provides several built-in middlewares to help with common tasks. Below are the available options and how to use them:

### CORS Middleware
- **Purpose:** Enables Cross-Origin Resource Sharing (CORS) for your APIs.
- **Usage:** Add `panther.middlewares.CORSMiddleware` to your global `MIDDLEWARES` list.
- **Configuration:** Requires specific global settings. See the [CORS Middleware documentation](cors.md) for configuration details.

### Monitoring Middleware
- **Purpose:** Logs request and connection data for monitoring and analytics.
- **Usage:** Add `panther.middlewares.MonitoringMiddleware` to your global `MIDDLEWARES` list.
- **Note:** This middleware or `WebsocketMonitoringMiddleware` is required if you want to use the `panther monitor` command.

### WebSocket Monitoring Middleware
- **Purpose:** Similar to `MonitoringMiddleware`, but specifically logs data for WebSocket connections.
- **Usage:** Add `panther.middlewares.WebsocketMonitoringMiddleware` to your global `MIDDLEWARES` list if you want to monitor WebSocket traffic.
- **Note:** This middleware or `MonitoringMiddleware` is required if you want to use the `panther monitor` command.

---

## Tips

- Use global middlewares for logic that should apply to all requests.
- Use per-API middlewares for logic specific to certain endpoints.
- Always ensure your `__call__` method is asynchronous and returns the appropriate value.
