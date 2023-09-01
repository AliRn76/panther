from __future__ import annotations

from panther import status
from panther.base_websocket import Websocket, WebsocketConnections
from panther.configs import config


class GenericWebsocket(Websocket):

    async def connect(self):
        """
        Check your conditions then `accept()` the connection
        """
        await self.accept()

    async def receive(self, text_data: str = None, bytes_data: bytes = None):
        """
        Receive `text_data` or `bytes_data` from the connection
        You may want to use json.loads() for the text_data
        """
        pass

    async def disconnect(self):
        """
        Just a demonstration how you can close a connection
        """
        return await self.close(code=status.WS_1000_NORMAL_CLOSURE, reason='I just want to close it')

    async def send(self, text_data: any = None, bytes_data: bytes = None):
        """
        We are using this method to send message to the client,
        You may want to override it with your custom scenario. (not recommended)
        """
        pass


async def send_message_to_websocket(connection_id: str, data: any):
    websocket_connections: WebsocketConnections = config['websocket_connections']
    if connection := websocket_connections.connections.get(connection_id):
        if isinstance(data, bytes):
            await connection.send(bytes_data=data)
        else:
            await connection.send(text_data=data)
