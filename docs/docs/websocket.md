Panther supports `WebSockets` routing just like `APIs`

## Structure & Requirements
### Create WebSocket Class

Create the `BookWebsocket()` which inherited from `GenericWebsocket` in `app/websockets.py`: 


```python
from panther.websocket import GenericWebsocket


class BookWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        print(f'{self.connection_id=}')

    async def receive(self, text_data: str = None, bytes_data: bytes = None):
        print(f'{text_data=}')
        print(f'{bytes_data=}')
```

> We are going to discuss it later ...

### Update URLs

Add the `BookWebsocket()` in `app/urls.py`:

```python
from app.websockets import BookWebsocket


urls = {
    'ws/book/': BookWebsocket,
}
```

## How It Works?
...

