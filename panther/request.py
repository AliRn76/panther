import logging
from collections.abc import Callable
from typing import Literal
from urllib.parse import parse_qsl

import orjson as json
from orjson import JSONDecodeError
from pydantic import ValidationError

from panther._utils import read_multipart_form_data
from panther.base_request import BaseRequest
from panther.exceptions import BadRequestAPIError, UnprocessableEntityError

logger = logging.getLogger('panther')


class Request(BaseRequest):
    def __init__(self, scope: dict, receive: Callable, send: Callable):
        self._data = ...
        self.validated_data = None  # It's been set in self.validate_input()
        super().__init__(scope=scope, receive=receive, send=send)

    @property
    def method(self) -> Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'QUERY']:
        return self.scope['method']

    @property
    def body(self) -> bytes:
        return self.__body

    def _content_type(self) -> tuple[str, dict[str, str]]:
        parts = [part.strip() for part in (self.headers.content_type or '').split(';')]
        media_type = parts[0].lower()
        parameters = {
            key.strip().lower(): value.strip().strip('"')
            for part in parts[1:]
            if '=' in part
            for key, value in [part.split('=', maxsplit=1)]
        }
        return media_type, parameters

    @property
    def data(self) -> dict | bytes:
        """Data before validation"""
        if self._data is ...:
            media_type, parameters = self._content_type()
            match media_type:
                case '' | 'application/json':
                    self._data = json.loads(self.__body or b'{}')
                case 'application/x-www-form-urlencoded':
                    self._data = {k.decode(): v.decode() for k, v in parse_qsl(self.__body)}
                case 'multipart/form-data' if boundary := parameters.get('boundary'):
                    self._data = read_multipart_form_data(boundary=boundary, body=self.__body)
                case unknown:
                    # We don't know the `content-type` so just pass the payload to user
                    logger.warning("'%s' Content-Type is not supported", unknown)
                    self._data = self.__body
        return self._data

    def validate_query_content(self) -> None:
        media_type, parameters = self._content_type()
        if not media_type:
            raise BadRequestAPIError(detail='Content-Type header is required for QUERY requests')

        if media_type == 'application/json' and not self.__body:
            raise BadRequestAPIError(detail='Content-Type is inconsistent with the QUERY request content')

        if media_type == 'multipart/form-data':
            boundary = parameters.get('boundary')
            if not boundary or f'--{boundary}'.encode() not in self.__body:
                raise BadRequestAPIError(detail='Content-Type is inconsistent with the QUERY request content')

        if media_type in {'application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'}:
            try:
                _ = self.data
            except (JSONDecodeError, UnicodeDecodeError):
                raise BadRequestAPIError(detail='Content-Type is inconsistent with the QUERY request content') from None

    async def read_body(self) -> None:
        """Read the entire body from an incoming ASGI message."""
        self.__body = b''
        more_body = True
        while more_body:
            message = await self.asgi_receive()
            self.__body += message.get('body', b'')
            more_body = message.get('more_body', False)

    def validate_data(self, model):
        try:
            data = self.data
            if isinstance(data, bytes):
                raise UnprocessableEntityError(detail='Content-Type is not valid')
            if data is None:
                raise BadRequestAPIError(detail='Request body is required')
            # `request` will be ignored in regular `BaseModel`
            self.validated_data = model(**data)
        except ValidationError as validation_error:
            error = {'.'.join(str(loc) for loc in e['loc']): e['msg'] for e in validation_error.errors()}
            raise BadRequestAPIError(detail=error) from None
        except JSONDecodeError:
            raise UnprocessableEntityError(detail='JSON Decode Error') from None
