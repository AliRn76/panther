from __future__ import annotations

from panther import status
from panther._utils import publish_to_ws_channel
from panther.base_websocket import Websocket, WebsocketConnections
from panther.configs import config
from panther.db.connection import redis


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

    async def disconnect(self):
        """
        Just a demonstration how you can `close()` a connection
        """
        await self.close(code=status.WS_1000_NORMAL_CLOSURE, reason='I just want to close it')

    async def send(self, text_data: any = None, bytes_data: bytes = None):
        """
        We are using this method to send message to the client,
        You may want to override it with your custom scenario. (not recommended)
        """
        return await super().send(text_data=text_data, bytes_data=bytes_data)


async def send_message_to_websocket(connection_id: str, data: any):
    if redis.is_connected:
        publish_to_ws_channel(connection_id=connection_id, data=data)
    else:
        websocket_connections: WebsocketConnections = config['websocket_connections']
        if connection := websocket_connections.connections.get(connection_id):
            if isinstance(data, bytes):
                await connection.send(bytes_data=data)
            else:
                await connection.send(text_data=data)
