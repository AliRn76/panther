import asyncio

from panther import Panther
from panther.app import API
from panther.test import APIClient, WebsocketClient
from panther.websocket import GenericWebsocket


@API()
async def health():
    return {'status': 'ok'}


class HelloWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.send('hello')


url_routing = {
    'health/': health,
    'ws/hello/': HelloWebsocket,
}

app = Panther(__name__, configs=__name__, urls=url_routing)


async def call_http_example():
    client = APIClient(app=app)
    response = await client.get('/health/')
    assert response.status_code == 200
    assert response.data == {'status': 'ok'}


def call_websocket_example():
    client = WebsocketClient(app=app)
    messages = client.connect('/ws/hello/')
    assert messages[0]['type'] == 'websocket.accept'
    assert messages[1]['text'] == 'hello'


if __name__ == '__main__':
    asyncio.run(call_http_example())
    call_websocket_example()
    print('Example client checks passed.')
