from dataclasses import dataclass
from typing import Callable

from panther.request import Address


@dataclass(frozen=True)
class WebsocketHeaders:
    upgrade: str
    sec_websocket_key: str
    sec_websocket_version: str
    connection: str
    host: str


class Websocket:
    def __init__(self, scope: dict, send: Callable):
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
        self.send = send
        self._data = None
        self._validated_data = None
        self._user = None
        self._headers: WebsocketHeaders | None = None
        self._params: dict | None = None

    async def accept(self):
        await self.send({"type": "websocket.accept"})

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
