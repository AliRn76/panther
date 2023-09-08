from __future__ import annotations

import orjson as json

from panther._utils import generate_ws_connection_id
from panther.base_request import BaseRequest
from panther.configs import config
from panther.logger import logger
from panther.utils import Singleton


class WebsocketConnections(Singleton):
    def __init__(self):
        self.connections = dict()
        self.connections_count = 0

    async def new_connection(self, connection: Websocket):
        await connection.connect()
        if connection.is_connected:
            self.connections_count += 1

            # Save New ConnectionID
            self.connections[connection.connection_id] = connection

    async def remove_connection(self, connection: Websocket):
        self.connections_count -= 1
        del self.connections[connection.connection_id]


class Websocket(BaseRequest):
    is_connected: bool = False

    async def connect(self):
        """
        Check your conditions then self.accept() the connection
        """
        await self.accept()

    async def accept(self, subprotocol: str = None, headers: dict = None):
        await self.asgi_send({'type': 'websocket.accept', 'subprotocol': subprotocol, 'headers': headers or {}})
        self.is_connected = True

        # Generate ConnectionID
        connection_id = generate_ws_connection_id()
        while connection_id in config['websocket_connections'].connections:
            connection_id = generate_ws_connection_id()

        # Set ConnectionID
        self.set_connection_id(connection_id)

    async def receive(self, text_data: any = None, bytes_data: bytes = None):
        pass

    async def send(self, text_data: any = None, bytes_data: bytes = None):
        if text_data:
            if not isinstance(text_data, str):
                text_data = json.dumps(text_data)
            await self.send_text(text_data=text_data)
        else:
            await self.send_bytes(bytes_data=bytes_data or b'')

    async def send_text(self, text_data: str = None):
        await self.asgi_send({'type': 'websocket.send', 'text': text_data})

    async def send_bytes(self, bytes_data: bytes = None):
        await self.asgi_send({'type': 'websocket.send', 'bytes': bytes_data})

    async def close(self, code: int = 1000, reason: str = ''):
        config['websocket_connections'].remove_connection(self)
        self.is_connected = False
        await self.asgi_send({'type': 'websocket.close', 'code': code, 'reason': reason})

    async def listen(self):
        while self.is_connected:
            response = await self.asgi_receive()
            if response['type'] == 'websocket.connect':
                continue

            if response['type'] == 'websocket.disconnect':
                break

            if 'text' in response:
                await self.receive(text_data=response['text'])
            else:
                await self.receive(bytes_data=response['bytes'])

    def set_path_variables(self, path_variables: dict):
        self._path_variables = path_variables

    @property
    def path_variables(self):
        return getattr(self, '_path_variables', {})

    def set_connection_id(self, connection_id):
        self._connection_id = connection_id

    @property
    def connection_id(self) -> str:
        connection_id = getattr(self, '_connection_id', None)
        if connection_id is None:
            logger.error('You should first `self.accept()` the connection then use the `self.connection_id`')
        return connection_id

