from types import NoneType

import orjson as json
from pydantic import BaseModel as PydanticBaseModel

ResponseDataTypes = list | tuple | set | dict | int | str | bool | NoneType
IterableDataTypes = list | tuple | set


class Response:
    content_type = 'application/json'

    def __init__(self, data: ResponseDataTypes = None, headers: dict = None, status_code: int = 200):
        """
        :param data: should be int | dict | list | tuple | set | str | bool | NoneType
            or instance of Pydantic.BaseModel
        :param status_code: should be int
        """

        # TODO: Handle bytes data
        data = self.clean_data_type(data)
        self.check_status_code(status_code)

        self._status_code = status_code
        self._data = data
        self._headers = headers

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def body(self) -> bytes:
        return json.dumps(self._data)

    @property
    def headers(self) -> dict:
        return {
            'content-type': self.content_type,
            'access-control-allow-origin': '*',
        } | (self._headers or {})

    def set_data(self, data) -> None:
        self._data = data

    @classmethod
    def check_status_code(cls, status_code: any):
        if not isinstance(status_code, int):
            error = f'Response "status_code" Should Be "int". ("{status_code}" -> {type(status_code)})'
            raise TypeError(error)

    @classmethod
    def clean_data_type(cls, data: any):
        """
        Make sure the response data is only ResponseDataTypes or Iterable of ResponseDataTypes
        """

        if issubclass(type(data), PydanticBaseModel):
            return data.model_dump()

        elif isinstance(data, IterableDataTypes):
            return [cls.clean_data_type(d) for d in data]

        elif isinstance(data, dict):
            return {key: cls.clean_data_type(value) for key, value in data.items()}

        elif isinstance(data, (int | str | bool | NoneType)):
            return data

        else:
            raise TypeError(f'Invalid Response Type: {type(data)}')


class HTMLResponse(Response):
    content_type = 'text/html; charset=utf-8'

    @property
    def body(self) -> bytes:
        return self._data.encode()


class PlainTextResponse(Response):
    content_type = 'text/plain; charset=utf-8'

    @property
    def body(self) -> bytes:
        return self._data.encode()
