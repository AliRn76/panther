from panther.websocket import GenericWebsocket


class UserWebsocket(GenericWebsocket):
    async def connect(self, user_id: int):
        print(f'{user_id=}')
        await self.accept()
        print(f'{self.connection_id=}')

    async def receive(self, text_data: str = None, bytes_data: bytes = None):
        print(f'{text_data=}')
        print(f'{bytes_data=}')

