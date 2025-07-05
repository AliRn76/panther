from collections.abc import Callable
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl

from panther.exceptions import InvalidPathVariableAPIError

if TYPE_CHECKING:
    from panther.db import Model


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

    def __contains__(self, item):
        return (item in self.__headers) or (item in self.__pythonic_headers)

    __repr__ = __str__

    @property
    def __dict__(self):
        return self.__headers

    def get_cookies(self) -> dict:
        """
        Example of `request.headers.cookie`:
            'csrftoken=aaa; sessionid=bbb; access_token=ccc; refresh_token=ddd'

        Example of `request.headers.get_cookies()`:
            {
                'csrftoken': 'aaa',
                'sessionid': 'bbb',
                'access_token': 'ccc',
                'refresh_token': 'ddd',
            }
        """
        if self.cookie:
            return {k.strip(): v for k, v in (c.split('=', maxsplit=1) for c in self.cookie.split(';'))}
        return {}


class Address:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def __str__(self):
        return f'{self.ip}:{self.port}'


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
            for variable, value in zip(found_path.strip('/').split('/'), self.path.strip('/').split('/'))
            if variable.startswith('<')
        }

    def clean_parameters(self, function_annotations: dict) -> dict:
        kwargs = self.path_variables.copy()

        for variable_name, variable_type in function_annotations.items():
            # Put Request/ Websocket In kwargs (If User Wants It)
            if issubclass(variable_type, BaseRequest):
                kwargs[variable_name] = self

            elif variable_name in kwargs:
                # Cast To Boolean
                if variable_type is bool:
                    value = kwargs[variable_name].lower()
                    if value in ['false', '0']:
                        kwargs[variable_name] = False
                    elif value in ['true', '1']:
                        kwargs[variable_name] = True
                    else:
                        raise InvalidPathVariableAPIError(value=kwargs[variable_name], variable_type=variable_type)

                # Cast To Int
                elif variable_type is int:
                    try:
                        kwargs[variable_name] = int(kwargs[variable_name])
                    except ValueError:
                        raise InvalidPathVariableAPIError(value=kwargs[variable_name], variable_type=variable_type)
        return kwargs
