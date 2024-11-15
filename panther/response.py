import asyncio
from sys import version_info
from types import NoneType
from typing import Generator, AsyncGenerator, Any, Type

if version_info >= (3, 11):
    from typing import LiteralString
else:
    from typing import TypeVar

    LiteralString = TypeVar('LiteralString')


import orjson as json
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader

from panther import status
from panther.configs import config
from panther._utils import to_async_generator
from panther.db.cursor import Cursor
from pantherdb import Cursor as PantherDBCursor
from panther.monitoring import Monitoring
from panther.pagination import Pagination

ResponseDataTypes = list | tuple | set | Cursor | PantherDBCursor | dict | int | float | str | bool | bytes | NoneType | Type[BaseModel]
IterableDataTypes = list | tuple | set | Cursor | PantherDBCursor
StreamingDataTypes = Generator | AsyncGenerator


class Response:
    content_type = 'application/json'

    def __init__(
        self,
        data: ResponseDataTypes = None,
        headers: dict | None = None,
        status_code: int = status.HTTP_200_OK,
        pagination: Pagination | None = None,
    ):
        """
        :param data: should be an instance of ResponseDataTypes
        :param headers: should be dict of headers
        :param status_code: should be int
        :param pagination: instance of Pagination or None
            The `pagination.template()` method will be used
        """
        self.headers = headers or {}
        self.pagination: Pagination | None = pagination
        if isinstance(data, Cursor):
            data = list(data)
        self.initial_data = data
        self.data = self.prepare_data(data=data)
        self.status_code = self.check_status_code(status_code=status_code)

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
    def bytes_headers(self) -> list[list[bytes]]:
        return [[k.encode(), str(v).encode()] for k, v in (self.headers or {}).items()]

    @headers.setter
    def headers(self, headers: dict):
        self._headers = headers

    def prepare_data(self, data: Any):
        """Make sure the response data is only ResponseDataTypes or Iterable of ResponseDataTypes"""
        if isinstance(data, (int | float | str | bool | bytes | NoneType)):
            return data

        elif isinstance(data, dict):
            return {key: self.prepare_data(value) for key, value in data.items()}

        elif issubclass(type(data), BaseModel):
            return data.model_dump()

        elif isinstance(data, IterableDataTypes):
            return [self.prepare_data(d) for d in data]

        else:
            msg = f'Invalid Response Type: {type(data)}'
            raise TypeError(msg)

    @classmethod
    def check_status_code(cls, status_code: Any):
        if not isinstance(status_code, int):
            error = f'Response `status_code` Should Be `int`. (`{status_code}` is {type(status_code)})'
            raise TypeError(error)
        return status_code

    async def apply_output_model(self, output_model: Type[BaseModel]):
        """This method is called in API.__call__"""

        # Dict
        if isinstance(self.data, dict):
            # Apply `validation_alias` (id -> _id)
            for field_name, field in output_model.model_fields.items():
                if field.validation_alias and field_name in self.data:
                    self.data[field.validation_alias] = self.data.pop(field_name)
            output = output_model(**self.data)
            if hasattr(output_model, 'prepare_response'):
                return await output.prepare_response(instance=self.initial_data, data=output.model_dump())
            return output.model_dump()

        # Iterable
        results = []
        if isinstance(self.data, IterableDataTypes):
            for i, d in enumerate(self.data):
                # Apply `validation_alias` (id -> _id)
                for field_name, field in output_model.model_fields.items():
                    if field.validation_alias and field_name in d:
                        d[field.validation_alias] = d.pop(field_name)

                output = output_model(**d)
                if hasattr(output_model, 'prepare_response'):
                    result = await output.prepare_response(instance=self.initial_data[i], data=output.model_dump())
                else:
                    result = output.model_dump()
                results.append(result)
            return results

        # Str | Bool | Bytes
        msg = 'Type of Response data is not match with `output_model`.\n*hint: You may want to remove `output_model`'
        raise TypeError(msg)

    async def send_headers(self, send, /):
        await send({'type': 'http.response.start', 'status': self.status_code, 'headers': self.bytes_headers})

    async def send_body(self, send, receive, /):
        await send({'type': 'http.response.body', 'body': self.body, 'more_body': False})

    async def send(self, send, receive, /, monitoring: Monitoring):
        await self.send_headers(send)
        await self.send_body(send, receive)
        await monitoring.after(self.status_code)

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
    def __init__(
        self,
        source: str | LiteralString | NoneType = None,
        path: str | NoneType = None,
        context: dict | NoneType = None,
        headers: dict | NoneType = None,
        status_code: int = status.HTTP_200_OK,
    ):
        """
        :param source: should be a string
        :param path: should be path of template file
        :param context: should be dict of items
        :param headers: should be dict of headers
        :param status_code: should be int
        """
        if path:
            template = config.JINJA_ENVIRONMENT.get_template(name=path)
        else:
            template = config.JINJA_ENVIRONMENT.from_string(source=source)
        super().__init__(
            data=template.render(context or {}),
            headers=headers,
            status_code=status_code,
        )
