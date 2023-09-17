from typing import Literal

import orjson as json

from panther._utils import read_multipart_form_data
from panther.base_request import BaseRequest
from panther.configs import config
from panther.logger import logger


class Request(BaseRequest):
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
                case ['multipart/form-data', boundary]:
                    self._data = read_multipart_form_data(boundary=boundary, body=self.__body)
                case [unknown]:
                    # We don't know the `content-type` so just pass the payload to user
                    if config['monitoring']:
                        logger.warning(f"'{unknown}' Content-Type is not supported")
                    self._data = self.__body
        return self._data

    def set_validated_data(self, validated_data) -> None:
        self._validated_data = validated_data

    @property
    def validated_data(self):
        """
        Return The Validated Data
        It has been set on API.validate_input() while request is happening.
        """
        return getattr(self, '_validated_data', None)

    async def read_body(self):
        """Read and return the entire body from an incoming ASGI message."""
        self.__body = b''
        more_body = True
        while more_body:
            message = await self.asgi_receive()
            self.__body += message.get('body', b'')
            more_body = message.get('more_body', False)
