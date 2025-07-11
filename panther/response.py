import asyncio
import logging
from collections.abc import AsyncGenerator, Generator
from dataclasses import dataclass
from http import cookies
from sys import version_info
from types import NoneType
from typing import Any, Literal

import jinja2

from panther.exceptions import APIError

if version_info >= (3, 11):
    from typing import LiteralString
else:
    from typing import TypeVar

    LiteralString = TypeVar('LiteralString')

import orjson as json
from pantherdb import Cursor as PantherDBCursor
from pydantic import BaseModel

from panther import status
from panther._utils import to_async_generator
from panther.configs import config
from panther.db.cursor import Cursor
from panther.pagination import Pagination

ResponseDataTypes = (
    list | tuple | set | Cursor | PantherDBCursor | dict | int | float | str | bool | bytes | NoneType | type[BaseModel]
)
IterableDataTypes = list | tuple | set | Cursor | PantherDBCursor
StreamingDataTypes = Generator | AsyncGenerator

logger = logging.getLogger('panther')


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
    """
    Usage Example:
        from panther.response import Response

        def my_api():
            data = {"message": "Hello, World!"}
            return Response(data=data)
    """

    content_type = 'application/json'

    def __init__(
        self,
        data: ResponseDataTypes = None,
        status_code: int = status.HTTP_200_OK,
        headers: dict | None = None,
        pagination: Pagination | None = None,
        set_cookies: Cookie | list[Cookie] | None = None,
    ):
        """
        :param data: should be an instance of ResponseDataTypes
        :param status_code: should be int
        :param headers: should be dict of headers
        :param pagination: an instance of Pagination or None
            The `pagination.template()` method will be used
        :param set_cookies: single cookie or list of cookies you want to set on the client.
            Set the `max-age` to `0` if you want to delete a cookie.
        """
        if isinstance(data, (Cursor, PantherDBCursor)):
            data = list(data)
        self.data = data
        self.status_code = status_code
        self.headers = {'Content-Type': self.content_type} | (headers or {})
        self.pagination: Pagination | None = pagination
        self.cookies = None
        if set_cookies:
            c = cookies.SimpleCookie()
            if not isinstance(set_cookies, list):
                set_cookies = [set_cookies]
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

    def __str__(self):
        if len(data := str(self.data)) > 30:
            data = f'{data:.27}...'
        return f'Response(status_code={self.status_code}, data={data})'

    __repr__ = __str__

    @property
    def body(self) -> bytes:
        def default(obj: Any):
            if isinstance(obj, BaseModel):
                return obj.model_dump()
            if isinstance(obj, (Cursor, PantherDBCursor)):
                return list(obj)
            if isinstance(obj, bytes):
                return f'raw bytes is not JSON serializable ({len(obj)} bytes)'
            raise TypeError(f'Type {type(obj)} not serializable')

        if isinstance(self.data, bytes):
            return self.data
        if self.data is None:
            return b''
        return json.dumps(self.data, default=default)

    @property
    def bytes_headers(self) -> list[tuple[bytes, bytes]]:
        headers = {'Content-Length': len(self.body)} | self.headers
        result = [(k.encode(), str(v).encode()) for k, v in headers.items()]
        if self.cookies:
            result += self.cookies
        return result

    async def send(self, send, receive):
        await send({'type': 'http.response.start', 'status': self.status_code, 'headers': self.bytes_headers})
        await send({'type': 'http.response.body', 'body': self.body, 'more_body': False})

    async def serialize_output(self, output_model: type[BaseModel]):
        """Serializes response data using the given output_model."""

        async def handle_output(obj):
            output = output_model(**obj) if isinstance(obj, dict) else output_model(**obj.model_dump())
            if hasattr(output_model, 'to_response'):
                return await output.to_response(instance=obj, data=output.model_dump())
            return output.model_dump()

        if isinstance(self.data, dict) or isinstance(self.data, BaseModel):
            self.data = await handle_output(self.data)

        elif isinstance(self.data, IterableDataTypes):
            results = []
            for d in self.data:
                if isinstance(d, dict) or isinstance(d, BaseModel):
                    results.append(await handle_output(d))
                else:
                    msg = 'Type of Response data is not match with `output_model`.\n*hint: You may want to remove `output_model`'
                    raise TypeError(msg)
            self.data = results

        else:
            msg = (
                'Type of Response data is not match with `output_model`.\n*hint: You may want to remove `output_model`'
            )
            raise TypeError(msg)


class StreamingResponse(Response):
    """
    Usage Example:
        from panther.response import StreamingResponse
        import time

        def my_generator():
            for i in range(5):
                time.sleep(1)
                yield f"Chunk {i}\n"

        def my_api():
            return StreamingResponse(data=my_generator())
    """

    content_type = 'application/octet-stream'

    def __init__(self, *args, **kwargs):
        self.connection_closed = False
        super().__init__(*args, **kwargs)

    async def listen_to_disconnection(self, receive):
        message = await receive()
        if message['type'] == 'http.disconnect':
            self.connection_closed = True

    @property
    def bytes_headers(self) -> list[tuple[bytes, bytes]]:
        result = [(k.encode(), str(v).encode()) for k, v in self.headers.items()]
        if self.cookies:
            result += self.cookies
        return result

    @property
    async def body(self) -> AsyncGenerator:
        if not isinstance(self.data, (Generator, AsyncGenerator)):
            raise TypeError(f'Type {type(self.data)} is not streamable, should be `Generator` or `AsyncGenerator`.')

        if isinstance(self.data, Generator):
            self.data = to_async_generator(self.data)

        async for chunk in self.data:
            if isinstance(chunk, bytes):
                yield chunk
            elif chunk is None:
                yield b''
            else:
                yield json.dumps(chunk)

    async def send(self, send, receive):
        # Send Headers
        await send({'type': 'http.response.start', 'status': self.status_code, 'headers': self.bytes_headers})
        # Send Body as chunks
        asyncio.create_task(self.listen_to_disconnection(receive=receive))
        async for chunk in self.body:
            if self.connection_closed:
                break
            await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})
        else:
            await send({'type': 'http.response.body', 'body': b'', 'more_body': False})


class HTMLResponse(Response):
    """
    Usage Example:
        from panther.response import HTMLResponse

        def my_api():
            html = "<h1>Hello, World!</h1>"
            return HTMLResponse(data=html)
    """

    content_type = 'text/html; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()


class PlainTextResponse(Response):
    """
    Usage Example:
        from panther.response import PlainTextResponse

        def my_api():
            return PlainTextResponse(data="Hello, World!")
    """

    content_type = 'text/plain; charset=utf-8'

    @property
    def body(self) -> bytes:
        if isinstance(self.data, bytes):
            return self.data
        return self.data.encode()


class TemplateResponse(HTMLResponse):
    """
    Usage Example:
        from panther.response import TemplateResponse

        def my_api():
            context = {"name": "Ali"}
            return TemplateResponse(name="index.html", context=context)
    """

    """
    You may want to declare `TEMPLATES_DIR` in your configs, default is '.'

    Example:
        TEMPLATES_DIR = 'templates/'

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
            try:
                template = config.JINJA_ENVIRONMENT.get_template(name=name)
            except jinja2.exceptions.TemplateNotFound:
                loaded_path = ' - '.join(
                    ' - '.join(loader.searchpath)
                    for loader in config.JINJA_ENVIRONMENT.loader.loaders
                    if isinstance(loader, jinja2.loaders.FileSystemLoader)
                )
                error = (
                    f'`{name}` Template Not Found.\n'
                    f'* Make sure `TEMPLATES_DIR` in your configs is correct, Current is {loaded_path}'
                )
                logger.error(error)
                raise APIError
        else:
            template = config.JINJA_ENVIRONMENT.from_string(source=source)
        super().__init__(
            data=template.render(context or {}),
            headers=headers,
            status_code=status_code,
        )


class RedirectResponse(Response):
    """
    Usage Example:
        from panther.response import RedirectResponse

        def my_api():
            return RedirectResponse(url="/new-location")
    """

    def __init__(
        self,
        url: str,
        headers: dict | None = None,
        status_code: int = status.HTTP_307_TEMPORARY_REDIRECT,
        set_cookies: list[Cookie] | None = None,
    ):
        headers = headers or {}
        headers['Location'] = url
        super().__init__(
            headers=headers,
            status_code=status_code,
            set_cookies=set_cookies,
        )
