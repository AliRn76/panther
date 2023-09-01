from panther.websocket import GenericWebsocket


class UserWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()

    async def receive(self, text: str = None, bytes: bytes = None):
        print(f'{text=}')
        print(f'{bytes=}')

    async def send(self):
        await self.send_text('Hello From UserWebsocket')

