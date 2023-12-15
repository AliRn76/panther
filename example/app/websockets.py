from panther.websocket import GenericWebsocket


class UserWebsocket(GenericWebsocket):
    async def connect(self, user_id: int):
        print(f'{user_id=}')
        await self.accept()
        print(f'{self.connection_id=}')

    async def receive(self, data: str | bytes):
        await self.send(data=data)
