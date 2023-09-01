from dataclasses import dataclass
from typing import Callable
import orjson as json

from panther import status
from panther.request import Address
from panther.utils import Singleton


@dataclass(frozen=True)
class WebsocketHeaders:
    upgrade: str
    sec_websocket_key: str
    sec_websocket_version: str
    connection: str
    host: str


class Websocket:
    def __init__(self, scope: dict, receive: Callable, send: Callable):
        """
        {
            'type': 'websocket',
            'asgi': {'version': '3.0', 'spec_version': '2.3'},
            'http_version': '1.1',
            'scheme': 'ws',
            'server': ('127.0.0.1', 8000),
            'client': ('127.0.0.1', 45360),
            'root_path': '',
            'path': '/',
            'raw_path': b'/',
            'query_string': b'',
            'state': {},
            'headers': [
                (b'host', b'127.0.0.1:8000'),
                (b'connection', b'Upgrade'),
                (b'sec-websocket-version', b'13'),
                (b'sec-websocket-key', b'Vi6QcgsQ5OvGxaWbLcf4GQ=='),
                (b'upgrade', b'websocket'),
            ],
            'subprotocols': [],
        }
        """

        self.scope = scope
        self.asgi_send = send
        self._receive = receive
        self._data = None
        self._validated_data = None
        self._user = None
        self._headers: WebsocketHeaders | None = None
        self._params: dict | None = None

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
            response = await self._receive()
            if response['type'] == 'websocket.connect':
                continue

            if response['type'] == 'websocket.disconnect':
                return

            if 'text' in response:
                await self.receive(text=response['text'])
            else:
                await self.receive(bytes=response['bytes'])

    @property
    def headers(self):
        _headers = {header[0].decode('utf-8'): header[1].decode('utf-8') for header in self.scope['headers']}
        if self._headers is None:
            self._headers = WebsocketHeaders(
                upgrade=_headers.pop('upgrade', None),
                sec_websocket_key=_headers.pop('sec_websocket_key', None),
                sec_websocket_version=_headers.pop('sec_websocket_version', None),
                connection=_headers.pop('connection', None),
                host=_headers.pop('host', None),
            )
        return self._headers

    @property
    def query_params(self) -> dict:
        if self._params is None:
            self._params = dict()
            if (query_string := self.scope['query_string']) != b'':
                query_string = query_string.decode('utf-8').split('&')
                for param in query_string:
                    k, *_, v = param.split('=')
                    self._params[k] = v
        return self._params

    @property
    def path(self) -> str:
        return self.scope['path']

    @property
    def server(self) -> Address:
        return Address(*self.scope['server'])

    @property
    def client(self) -> Address:
        return Address(*self.scope['client'])

    @property
    def http_version(self) -> str:
        return self.scope['http_version']

    @property
    def scheme(self) -> str:
        return self.scope['scheme']

    @property
    def user(self):
        return self._user

    def set_user(self, user) -> None:
        self._user = user


class WebsocketConnections(Singleton):
    def __init__(self):
        self.connections = dict()
        self.connections_count = 0

    async def new_connection(self, connection: Websocket):
        await connection.connect()  # TODO: Check user accepted or not
        self.connections_count += 1
        self.connections[self.connections_count] = connection
        return self.connections_count


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
