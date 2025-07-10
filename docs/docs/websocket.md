# WebSocket Support in Panther

**WebSockets** enable you to build interactive, real-time features such as chat, notifications, and live updates.

---

## Structure & Requirements

### Creating a WebSocket Class
Create a WebSocket handler class in `app/websockets.py` by inheriting from `GenericWebsocket`:

```python title="app/websockets.py" linenums="1"
from panther.websocket import GenericWebsocket

class BookWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        print(f'{self.connection_id=}')

    async def receive(self, data: str | bytes):
        # Echo the received message back to the client
        await self.send(data=data)
```

### Registering WebSocket URLs
Register your WebSocket class in `app/urls.py`:

```python title="app/urls.py" linenums="1"
from app.websockets import BookWebsocket

urls = {
    'ws/book/': BookWebsocket,
}
```

> Panther supports WebSocket routing just like APIs.

---

## How It Works
1. **Client Connection:** The client connects to your `ws/book/` URL using the WebSocket protocol.
2. **Connection Handling:** The `connect()` method of your WebSocket class is called.
3. **Validation:** You can validate the connection using `self.headers`, `self.query_params`, etc.
4. **Accept/Reject:** Accept the connection with `self.accept()`. If not accepted, it is rejected by default.
5. **Connection ID:** Each connection gets a unique `connection_id` (accessible via `self.connection_id`). You may want to store this in a database or cache.
6. **Receiving Messages:** Incoming messages are handled by the `receive()` method. Messages can be `str` or `bytes`.
7. **Sending Messages:**
    - **Within the WebSocket class:** Use `self.send(data)`.
    - **Outside the WebSocket class:** Use `send_message_to_websocket()`:
      ```python
      from panther.websocket import send_message_to_websocket
      await send_message_to_websocket(connection_id='7e82d57c9ec0478787b01916910a9f45', data='New Message From WS')
      ```

---

## Advanced Usage

### Authentication
You can enable authentication in your WebSocket class by setting `auth` to an async function or a class with an async `__call__` method. Panther will use this callable to authenticate the user. 

- If you do not set `auth`, Panther will use the default `WS_AUTHENTICATION` from your configuration **only if the request contains an authorization header/ cookie/ param/ etc.**. 
- If there is no authorization header, authentication is bypassed and `self.user` will be `None`.

There are several built-in options, but we recommend `QueryParamJWTAuthentication` for WebSocket authentication.

```python
WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```

This will set `self.user` to a `UserModel` instance or `None`. The connection will be rejected if any exception occurs during authentication.

```python title="app/websockets.py" linenums="1"
from panther.websocket import GenericWebsocket
from app.authentications import MyAuthenticationClass

class MyWebSocket(GenericWebsocket):
    auth = MyAuthenticationClass  # Or use an async function
    
    async def connect(self):
        print(self.user)
        ...
```

> **Note:** When authentication is bypassed (no authorization header), `self.user` will be `None` and you must rely on permissions to check the user and their authorization.

### Permissions
You can implement your authorization logic using permission classes or functions. Any async function or class with an async `__call__` method can be used as a permission. Panther will call each permission (asynchronously). 

- If any return `False`, the connection will be rejected.

Pass a list of permission callables to your WebSocket class. 

- If you pass a single permission, it will be automatically wrapped in a list.

> Each permission must be async (either an async function or a class with an async `__call__`).

**Example Permission Function:**

```python title="app/permissions.py" linenums="1"
from panther.websocket import Websocket

async def custom_permission(request: Websocket) -> bool:
    return True
```

**Example Permission Class:**

```python title="app/permissions.py" linenums="1"
from panther.websocket import Websocket
from panther.permissions import BasePermission

class CustomPermission(BasePermission):
    async def __call__(self, request: Websocket) -> bool:
        return True
```

```python title="app/websockets.py" linenums="1"
from panther.websocket import GenericWebsocket
from app.permissions import custom_permission, CustomPermission

class MyWebSocket(GenericWebsocket):
    permissions = [custom_permission, CustomPermission]  # Or just one
    
    async def connect(self):
        ...
```

### Multiple Workers & Redis
- **Recommended:** For running WebSockets with multiple workers, add Redis to your configuration. [See Adding Redis](redis.md)
- **Without Redis:** If you do not use Redis but want to run WebSockets with multiple workers (e.g., with Gunicorn), use the `--preload` flag:
  ```shell
  gunicorn -w 10 -k uvicorn.workers.UvicornWorker main:app --preload
  ```
- **Uvicorn Limitation:** WebSockets do not work properly when using uvicorn directly with the `--workers` flag (e.g., `uvicorn main:app --workers 4`). This is because each worker process maintains its own separate WebSocket connections, and there's no shared state between workers. Use Gunicorn with the `--preload` flag or add Redis for proper WebSocket support with multiple workers.

### Closing Connections
- **Within the WebSocket class:**
  ```python
  from panther import status
  await self.close(code=status.WS_1000_NORMAL_CLOSURE, reason='Closing connection')
  ```
- **Outside the WebSocket class:**
  ```python
  from panther import status
  from panther.websocket import close_websocket_connection
  await close_websocket_connection(connection_id='7e82d57c9ec0478787b01916910a9f45', code=status.WS_1008_POLICY_VIOLATION, reason='Closing connection')
  ```

### Path Variables
You can define path variables in your WebSocket URL. These will be passed to the `connect()` method:

```python linenums="1"
from panther.websocket import GenericWebsocket

class UserWebsocket(GenericWebsocket):
    async def connect(self, user_id: int, room_id: str):
        await self.accept()

urls = {
    '/ws/<user_id>/<room_id>/': UserWebsocket
}
```

---

## Example

### Example Client Code
**Here's a simple example using JavaScript:**

```js title="websocket.js" linenums="1"
const ws = new WebSocket('ws://127.0.0.1:8000/ws/book/');
ws.onopen = () => {
    ws.send('Hello, server!');
};
ws.onmessage = (event) => {
    console.log('Received:', event.data);
};
ws.onclose = () => {
    console.log('Connection closed');
};
```

### Echo Example
**Full echo example with WebSocket:**

```python title="main.py" linenums="1"
from panther import Panther
from panther.app import GenericAPI
from panther.response import HTMLResponse
from panther.websocket import GenericWebsocket

class EchoWebsocket(GenericWebsocket):
    async def connect(self, **kwargs):
        await self.accept()

    async def receive(self, data: str | bytes):
        await self.send(data)

class MainPage(GenericAPI):
    def get(self):
        template = """
        <input id="msg"><button onclick="s.send(msg.value)">Send</button>
        <ul id="log"></ul>
        <script>
            const s = new WebSocket('ws://127.0.0.1:8000/ws');
            s.onmessage = e => log.innerHTML += `<li><- ${msg.value}</li><li>-> ${e.data}</li>`;
        </script>
        """
        return HTMLResponse(template)

url_routing = {
    '': MainPage,
    'ws': EchoWebsocket,
}
app = Panther(__name__, configs=__name__, urls=url_routing)
```
**Run** with `panther run main:app` and **visit** `http://127.0.0.1:8000`.

---

## Tips & Notes
- **Connection Validation:** Always validate connections in `connect()` using headers or query parameters as needed.
- **Connection IDs:** Store `connection_id` if you need to send messages to clients outside the WebSocket class.
- **Multiple Workers:** Use Redis for scaling WebSockets across multiple workers.
- **Error Handling:** Implement error handling in your WebSocket methods for production use.
- **Security:** Always validate and sanitize incoming data.

---

Enjoy building with Panther WebSockets!

