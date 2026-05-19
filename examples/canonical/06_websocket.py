from panther import Panther
from panther.websocket import GenericWebsocket


class EchoWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.send('Connected to Panther WebSocket')

    async def receive(self, data: str | bytes):
        await self.send(f'Echo: {data}')


url_routing = {
    'ws/echo/': EchoWebsocket,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
