from collections import namedtuple
from dataclasses import dataclass
from typing import Callable

import orjson as json

from panther._utils import read_multipart_form_data


@dataclass(frozen=True)
class Headers:
    accept_encoding: str
    content_length: int
    authorization: str
    content_type: str
    user_agent: str
    connection: str
    accept: str
    host: str

    sec_websocket_version: int
    sec_websocket_key: str
    upgrade: str


Address = namedtuple('Client', ['ip', 'port'])


class BaseRequest:
    def __init__(self, scope: dict, receive: Callable, send: Callable):
        self.scope = scope
        self.asgi_send = send
        self.asgi_receive = receive
        self._data = ...
        self._validated_data = None
        self._user = None
        self._headers: Headers | None = None
        self._params: dict | None = None

    @property
    def headers(self):
        _headers = {header[0].decode('utf-8'): header[1].decode('utf-8') for header in self.scope['headers']}
        if self._headers is None:
            self._headers = Headers(
                accept_encoding=_headers.pop('accept-encoding', None),
                content_length=_headers.pop('content_length', None),
                authorization=_headers.pop('authorization', None),
                content_type=_headers.pop('content-type', None),
                user_agent=_headers.pop('user-agent', None),
                connection=_headers.pop('connection', None),
                accept=_headers.pop('accept', None),
                host=_headers.pop('host', None),
                sec_websocket_version=_headers.pop('sec_websocket_version', None),
                sec_websocket_key=_headers.pop('sec_websocket_key', None),
                upgrade=_headers.pop('upgrade', None),
                # TODO: Others ...
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
