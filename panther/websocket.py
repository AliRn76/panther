from __future__ import annotations

import orjson as json

from panther import status
from panther.base_request import BaseRequest
from panther.utils import Singleton


class WebsocketConnections(Singleton):
    def __init__(self):
        self.connections = dict()
        self.connections_count = 0

    async def new_connection(self, connection: GenericWebsocket):
        await connection.connect()  # TODO: Check user accepted or not
        self.connections_count += 1
        self.connections[self.connections_count] = connection
        connection.set_connection_id(self.connections_count)


class Websocket(BaseRequest):
    async def connect(self):
        """
        Check your conditions then self.accept() the connection
        """
        return await self.accept()

    async def accept(self, subprotocol: str = None, headers: dict = None):
        await self.asgi_send({"type": "websocket.accept", "subprotocol": subprotocol, "headers": headers or {}})

    async def receive(self, text: any = None, bytes: bytes = None):
        pass

    async def send_text(self, text: any = None):
        await self.asgi_send({"type": "websocket.send", "text": json.dumps(text or '')})

    async def send_bytes(self, bytes: bytes = None):
        await self.asgi_send({"type": "websocket.send", "bytes": bytes})

    async def close(self, code: int = 1000, reason: str = ''):
        await self.asgi_send({"type": "websocket.close", 'code': code, 'reason': reason})

    async def listen(self):
        while True:
            response = await self.asgi_receive()
            if response['type'] == 'websocket.connect':
                continue

            if response['type'] == 'websocket.disconnect':
                return

            if 'text' in response:
                await self.receive(text=response['text'])
            else:
                await self.receive(bytes=response['bytes'])

    def set_path_variables(self, path_variables: dict):
        self._path_variables = path_variables

    @property
    def path_variables(self):
        return getattr(self, 'path_variables', {})

    def connection_id(self):
        return self.__connection_id

    def set_connection_id(self, connection_id):
        self.__connection_id = connection_id


class GenericWebsocket(Websocket):

    async def connect(self):
        """
        Check your conditions then accept the connection
        """
        await self.accept()

    async def receive(self, text: str = None, bytes: bytes = None):
        """
        Receive text or bytes from the connection
        You may want to use json.loads() for the text
        """
        pass

    async def send(self):
        """
        await self.send_text('Hello')
            or
        await self.send_bytes(b'This is sample data')
        """

    async def disconnect(self):
        """
        Just a demonstration how you can close a connection
        """
        return await self.close(code=status.WS_1000_NORMAL_CLOSURE, reason='I just want to close it')
