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
        self.validated_data = None  # It's been set in API.validate_input()
        super().__init__(scope=scope, receive=receive, send=send)

    @property
    def method(self) -> Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        return self.scope['method']

    @property
    def data(self) -> dict | bytes:
        """Data before validation"""
        if self._data is ...:
            match (self.headers.content_type or '').split('; boundary='):
                case ['' | 'application/json']:
                    self._data = json.loads(self.__body or b'{}')
                case ['application/x-www-form-urlencoded']:
                    self._data = {k.decode(): v.decode() for k, v in parse_qsl(self.__body)}
                case ['multipart/form-data', boundary]:
                    self._data = read_multipart_form_data(boundary=boundary, body=self.__body)
                case [unknown]:
                    # We don't know the `content-type` so just pass the payload to user
                    logger.warning(f"'{unknown}' Content-Type is not supported")
                    self._data = self.__body
        return self._data

    async def read_body(self) -> None:
        """Read the entire body from an incoming ASGI message."""
        self.__body = b''
        more_body = True
        while more_body:
            message = await self.asgi_receive()
            self.__body += message.get('body', b'')
            more_body = message.get('more_body', False)

    def validate_data(self, model):
        if isinstance(self.data, bytes):
            raise UnprocessableEntityError(detail='Content-Type is not valid')
        if self.data is None:
            raise BadRequestAPIError(detail='Request body is required')
        try:
            # `request` will be ignored in regular `BaseModel`
            self.validated_data = model(**self.data)
        except ValidationError as validation_error:
            error = {'.'.join(str(loc) for loc in e['loc']): e['msg'] for e in validation_error.errors()}
            raise BadRequestAPIError(detail=error)
        except JSONDecodeError:
            raise UnprocessableEntityError(detail='JSON Decode Error')
