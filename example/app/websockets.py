from panther.websocket import GenericWebsocket


class UserWebsocket(GenericWebsocket):
    async def connect(self):
        print(f'{self.connection_id=}')
        await self.accept()
        print(f'{self.connection_id=}')
        # await self.close()

    async def receive(self, text_data: str = None, bytes_data: bytes = None):
        print(f'{text_data=}')
        print(f'{bytes_data=}')

