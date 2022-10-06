from collections import namedtuple

import orjson as json
from dataclasses import dataclass


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


Client = namedtuple('Client', ['ip', 'port'])


class Request:
    def __init__(self, scope: dict, body: bytes):
        """
        {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': '2.3'},
        'http_version': '1.1', 'server': ('127.0.0.1', 8000), 'client': ('127.0.0.1', 35064),
        'scheme': 'http', 'root_path': '', 'headers': [
            (b'content-type', b'application/json'),
            (b'user-agent', b'PostmanRuntime/7.29.2'),
            (b'accept', b'*/*'),
            (b'postman-token', b'3e78fbf3-df2f-41bd-bedc-cf6027fa4fe6'),
            (b'host', b'127.0.0.1:8000'),
            (b'accept-encoding', b'gzip, deflate, br'),
            (b'connection', b'keep-alive'),
            (b'content-length', b'55')
        ],
        'method': 'GET', 'path': '/list/', 'raw_path': b'/list/', 'query_string': b''}
        """
        self.scope = scope
        self._body = body
        self._data = None
        self._user = None

    @property
    def headers(self):
        _headers = {header[0].decode('utf-8'): header[1].decode('utf-8') for header in self.scope['headers']}

        # logger.debug(_headers)
        return Headers(
            accept_encoding=_headers.pop('accept-encoding', None),
            content_length=_headers.pop('content_length', None),
            authorization=_headers.pop('authorization',  b''),
            content_type=_headers.pop('content-type', None),
            user_agent=_headers.pop('user-agent', None),
            connection=_headers.pop('connection', None),
            accept=_headers.pop('accept', None),
            host=_headers.pop('host', None),
            # TODO: Others ...
        )

    @property
    def query_params(self):
        query_string = self.scope['query_string'].decode('utf-8').split('&')
        params = {}
        for param in query_string:
            k, *_, v = param.split('=')
            params[k] = v
        return params

    @property
    def method(self):
        return self.scope['method']

    @property
    def path(self):
        return self.scope['path']

    @property
    def server(self):
        return self.scope['server']

    @property
    def client(self):
        return Client(*self.scope['client'])

    @property
    def http_version(self):
        return self.scope['http_version']

    @property
    def scheme(self):
        return self.scope['scheme']

    @property
    def data(self):
        from panther.logger import logger

        if self._data:
            return self._data

        body = self._body.decode('utf-8') or {}
        if self.headers.content_type is None:
            # logger.error(f'request content-type is None.')
            _data = body
        elif self.headers.content_type == 'application/json':
            _data = json.loads(body)
        elif self.headers.content_type[:19] == 'multipart/form-data':
            # TODO: Handle Multipart Form Data
            logger.error(f"We Don't Handle Multipart Request Yet.")
            _data = None
        else:
            logger.error(f'{self.headers.content_type} Is Not Supported.')
            _data = None

        # return {'id': 1, 'username': 'ali', 'password': '1123'}  # TODO: For Testing ...
        return _data

    def set_data(self, data) -> None:
        self._data = data

    @property
    def user(self):
        return self._user

    def set_user(self, user) -> None:
        self._user = user
