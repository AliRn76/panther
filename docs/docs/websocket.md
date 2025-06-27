# WebSocket Support in Panther

**WebSockets** enable you to build interactive, real-time features such as chat, notifications, and live updates.

---

## Structure & Requirements

### Creating a WebSocket Class
Create a WebSocket handler class in `app/websockets.py` by inheriting from `GenericWebsocket`:

```python
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

```python
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
You can enable authentication in your WebSocket class by setting `auth = True` and specifying your authentication class in the configuration with `WS_AUTHENTICATION`. Panther will use the `authentication()` method of this class to authenticate the user. There are several built-in options, but we recommend `QueryParamJWTAuthentication` for WebSocket authentication.

```python
WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```

This will set `self.user` to a `UserModel` instance or `None`. The connection will be rejected if any exception occurs during authentication.

```python title="app/websockets.py" linenums="1"
from panther.websocket import GenericWebsocket

class MyWebSocket(GenericWebsocket):
    auth = True
    
    async def connect(self):
        print(self.user)
        ...
```

### Permissions
You can implement your authorization logic using permission classes. Any class that inherits from `panther.permissions.BasePermission` or implements an `authorization()` method can be used as a permission class.

Pass a list of permission classes to your WebSocket class, and Panther will call each class's `authorization()` method. If any return `False`, the connection will be rejected.

> The `authorization()` method should be an `async classmethod`.

```python title="app/websockets.py" linenums="1"
from panther.websocket import Websocket, GenericWebsocket
from panther.permissions import BasePermission

class MyPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Websocket) -> bool:
        return True

class MyWebSocket(GenericWebsocket):
    permissions = [MyPermission]
    
    async def connect(self):
        ...
```


### Multiple Workers & Redis
- **Recommended:** For running WebSockets with multiple workers, add Redis to your configuration. [See Adding Redis](/redis/)
- **Without Redis:** If you do not use Redis but want to run WebSockets with multiple workers (e.g., with Gunicorn), use the `--preload` flag:
  ```shell
  gunicorn -w 10 -k uvicorn.workers.UvicornWorker main:app --preload
  ```

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

```python
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

```js
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

