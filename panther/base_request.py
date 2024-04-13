from collections import namedtuple
from collections.abc import Callable
from urllib.parse import parse_qsl

from panther.db import Model
from panther.exceptions import InvalidPathVariableAPIError


class Headers:
    accept: str
    accept_encoding: str
    accept_language: str
    authorization: str
    cache_control: str
    connection: str
    content_length: str
    content_type: str
    host: str
    origin: str
    pragma: str
    referer: str
    sec_fetch_dest: str
    sec_fetch_mode: str
    sec_fetch_site: str
    user_agent: str

    upgrade: str
    sec_websocket_version: str
    sec_websocket_key: str

    def __init__(self, headers: list):
        self.__headers = {header[0].decode('utf-8'): header[1].decode('utf-8') for header in headers}
        self.__pythonic_headers = {k.lower().replace('-', '_'): v for k, v in self.__headers.items()}

    def __getattr__(self, item: str):
        if result := self.__pythonic_headers.get(item):
            return result
        return self.__headers.get(item)

    def __getitem__(self, item: str):
        if result := self.__headers.get(item):
            return result
        return self.__pythonic_headers.get(item)

    def __str__(self):
        items = ', '.join(f'{k}={v}' for k, v in self.__headers.items())
        return f'Headers({items})'

    __repr__ = __str__

    @property
    def __dict__(self):
        return self.__headers


Address = namedtuple('Address', ['ip', 'port'])


class BaseRequest:
    def __init__(self, scope: dict, receive: Callable, send: Callable):
        self.scope = scope
        self.asgi_send = send
        self.asgi_receive = receive
        self._headers: Headers | None = None
        self._params: dict | None = None
        self.user: Model | None = None
        self.path_variables: dict | None = None

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            self._headers = Headers(self.scope['headers'])
        return self._headers

    @property
    def query_params(self) -> dict:
        if self._params is None:
            self._params = {k: v for k, v in parse_qsl(self.scope['query_string'].decode('utf-8'))}
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

    def collect_path_variables(self, found_path: str):
        self.path_variables = {
            variable.strip('< >'): value
            for variable, value in zip(
                found_path.strip('/').split('/'),
                self.path.strip('/').split('/')
            )
            if variable.startswith('<')
        }

    def clean_parameters(self, func: Callable) -> dict:
        kwargs = self.path_variables.copy()

        for variable_name, variable_type in func.__annotations__.items():
            # Put Request/ Websocket In kwargs (If User Wants It)
            if issubclass(variable_type, BaseRequest):
                kwargs[variable_name] = self

            elif variable_name in kwargs:
                # Cast To Boolean
                if variable_type is bool:
                    kwargs[variable_name] = kwargs[variable_name].lower() not in ['false', '0']

                # Cast To Int
                elif variable_type is int:
                    try:
                        kwargs[variable_name] = int(kwargs[variable_name])
                    except ValueError:
                        raise InvalidPathVariableAPIError(value=kwargs[variable_name], variable_type=variable_type)
        return kwargs
