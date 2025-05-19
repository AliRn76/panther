import asyncio
from dataclasses import dataclass
from http import cookies
from sys import version_info
from types import NoneType
from typing import Generator, AsyncGenerator, Any, Type, Literal

if version_info >= (3, 11):
    from typing import LiteralString
else:
    from typing import TypeVar

    LiteralString = TypeVar('LiteralString')

import orjson as json
from pydantic import BaseModel

from panther import status
from panther.configs import config
from panther._utils import to_async_generator
from panther.db.cursor import Cursor
from pantherdb import Cursor as PantherDBCursor
from panther.pagination import Pagination

ResponseDataTypes = list | tuple | set | Cursor | PantherDBCursor | dict | int | float | str | bool | bytes | NoneType | Type[BaseModel]
IterableDataTypes = list | tuple | set | Cursor | PantherDBCursor
StreamingDataTypes = Generator | AsyncGenerator


@dataclass(slots=True)
class Cookie:
    """
    path: [Optional] Indicates the path that must exist in the requested URL for the browser to send the Cookie header.
        Default is `/`
    domain: [Optional] Defines the host to which the cookie will be sent.
        Default is the host of the current document URL, not including subdomains.
    max_age: [Optional] Indicates the number of seconds until the cookie expires.
        A zero or negative number will expire the cookie immediately.
    secure: [Optional] Indicates that the cookie is sent to the server
        only when a request is made with the https: scheme (except on localhost)
    httponly: [Optional] Forbids JavaScript from accessing the cookie,
        for example, through the `Document.cookie` property.
    samesite: [Optional] Controls whether a cookie is sent with cross-site requests or not,
        `lax` is the default behavior if not specified.
    expires: [Deprecated] In HTTP version 1.1, `expires` was deprecated and replaced with the easier-to-use `max-age`
    """
    key: str
    value: str
    domain: str = None
    max_age: int = None
    secure: bool = False
    httponly: bool = False
    samesite: Literal['none', 'lax', 'strict'] = 'lax'
    path: str = '/'


class Response:
    content_type = 'application/json'

    def __init__(
        self,
        data: ResponseDataTypes = None,
        status_code: int = status.HTTP_200_OK,
        headers: dict | None = None,
        pagination: Pagination | None = None,
        set_cookies: list[Cookie] | None = None
    ):
        """
        :param data: should be an instance of ResponseDataTypes
        :param status_code: should be int
        :param headers: should be dict of headers
        :param pagination: an instance of Pagination or None
            The `pagination.template()` method will be used
        :param set_cookies: list of cookies you want to set on the client
            Set the `max_age` to `0` if you want to delete a cookie
        """
        headers = headers or {}
        self.pagination: Pagination | None = pagination
        if isinstance(data, Cursor):
            data = list(data)
        self.initial_data = data
        self.data = self.prepare_data(data=data)
        self.status_code = self.check_status_code(status_code=status_code)
        self.cookies = None
        if set_cookies:
            c = cookies.SimpleCookie()
            for cookie in set_cookies:
                c[cookie.key] = cookie.value
                c[cookie.key]['path'] = cookie.path
                c[cookie.key]['secure'] = cookie.secure
                c[cookie.key]['httponly'] = cookie.httponly
                c[cookie.key]['samesite'] = cookie.samesite
                if cookie.domain is not None:
                    c[cookie.key]['domain'] = cookie.domain
                if cookie.max_age is not None:
                    c[cookie.key]['max-age'] = cookie.max_age
            self.cookies = [(b'Set-Cookie', cookie.OutputString().encode()) for cookie in c.values()]
        self.headers = headers

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data

        if self.data is None:
            return b''
        return json.dumps(self.data)

    @property
    def headers(self) -> dict:
        return {
            'Content-Type': self.content_type,
            'Content-Length': len(self.body),
            'Access-Control-Allow-Origin': '*',
        } | self._headers

    @property
    def bytes_headers(self) -> list[tuple[bytes]]:
        result = [(k.encode(), str(v).encode()) for k, v in (self.headers or {}).items()]
        if self.cookies:
            result.extend(self.cookies)
        return result

    @headers.setter
    def headers(self, headers: dict):
        self._headers = headers

    @classmethod
    def prepare_data(cls, data: Any):
        """Make sure the response data is only ResponseDataTypes or Iterable of ResponseDataTypes"""
        if isinstance(data, (int | float | str | bool | bytes | NoneType)):
            return data

        elif isinstance(data, dict):
            return {key: cls.prepare_data(value) for key, value in data.items()}

        elif issubclass(type(data), BaseModel):
            return data.model_dump()

        elif isinstance(data, IterableDataTypes):
            return [cls.prepare_data(d) for d in data]

        else:
            msg = f'Invalid Response Type: {type(data)}'
            raise TypeError(msg)

    @classmethod
    def check_status_code(cls, status_code: Any):
        if not isinstance(status_code, int):
            error = f'Response `status_code` Should Be `int`. (`{status_code}` is {type(status_code)})'
            raise TypeError(error)
        return status_code

    async def send_headers(self, send, /):
        await send({'type': 'http.response.start', 'status': self.status_code, 'headers': self.bytes_headers})

    async def send_body(self, send, receive, /):
        await send({'type': 'http.response.body', 'body': self.body, 'more_body': False})

    async def send(self, send, receive, /):
        await self.send_headers(send)
        await self.send_body(send, receive)

    def __str__(self):
        if len(data := str(self.data)) > 30:
            data = f'{data:.27}...'
        return f'Response(status_code={self.status_code}, data={data})'

    __repr__ = __str__


class StreamingResponse(Response):
    content_type = 'application/octet-stream'

    def __init__(self, *args, **kwargs):
        self.connection_closed = False
        super().__init__(*args, **kwargs)

    async def listen_to_disconnection(self, receive):
        message = await receive()
        if message['type'] == 'http.disconnect':
            self.connection_closed = True

    def prepare_data(self, data: any) -> AsyncGenerator:
        if isinstance(data, AsyncGenerator):
            return data
        elif isinstance(data, Generator):
            return to_async_generator(data)
        msg = f'Invalid Response Type: {type(data)}'
        raise TypeError(msg)

    @property
    def headers(self) -> dict:
        return {
            'Content-Type': self.content_type,
            'Access-Control-Allow-Origin': '*',
        } | self._headers

    @headers.setter
    def headers(self, headers: dict):
        self._headers = headers

    @property
    async def body(self) -> AsyncGenerator:
        async for chunk in self.data:
            if isinstance(chunk, bytes):
                yield chunk
            elif chunk is None:
                yield b''
            else:
                yield json.dumps(chunk)

    async def send_body(self, send, receive, /):
        asyncio.create_task(self.listen_to_disconnection(receive))
        async for chunk in self.body:
            if self.connection_closed:
                break
            await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
        else:
            await send({'type': 'http.response.body', 'body': b'', 'more_body': False})


class HTMLResponse(Response):
    content_type = 'text/html; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()


class PlainTextResponse(Response):
    content_type = 'text/plain; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()


class TemplateResponse(HTMLResponse):
    """
    You may want to declare `TEMPLATES_DIR` in your configs

    Example:
        TEMPLATES_DIR = 'templates/'
            or
        TEMPLATES_DIR = '.'
    """
    def __init__(
        self,
        source: str | LiteralString | NoneType = None,
        name: str | NoneType = None,
        context: dict | NoneType = None,
        headers: dict | NoneType = None,
        status_code: int = status.HTTP_200_OK,
    ):
        """
        :param source: should be a string
        :param name: name of the template file (should be with its extension, e.g. index.html)
        :param context: should be dict of items
        :param headers: should be dict of headers
        :param status_code: should be int
        """
        if name:
            template = config.JINJA_ENVIRONMENT.get_template(name=name)
        else:
            template = config.JINJA_ENVIRONMENT.from_string(source=source)
        super().__init__(
            data=template.render(context or {}),
            headers=headers,
            status_code=status_code,
        )


class RedirectResponse(Response):
    def __init__(
        self,
        url: str,
        headers: dict | None = None,
        status_code: int = status.HTTP_307_TEMPORARY_REDIRECT,
        set_cookies: list[Cookie] | None = None
    ):
        headers = headers or {}
        headers['Location'] = url
        super().__init__(
            headers=headers,
            status_code=status_code,
            set_cookies=set_cookies,
        )
