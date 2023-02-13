from types import NoneType

import orjson as json


class Response:
    def __init__(self, data: dict | list | tuple | str | bool = None, status_code: int = 200):
        """
        :param data: should be dict, list, tuple, str, bool
        :param status_code: should be int
        """
        if type(data) not in [dict, list, tuple, str, bool, NoneType]:
            raise TypeError(f"Response data can't be '{type(data).__name__}'")
        self._status_code = status_code
        self._data = data
        # TODO: Add Header To Response

    @property
    def status_code(self) -> int:
        if isinstance(self._status_code, int):
            return self._status_code
        else:
            raise TypeError(f"Response 'status_code' Should Be int. ('{self._status_code}' -> {type(self._status_code)})")

    @property
    def data(self) -> bytes:
        return json.dumps(self._data)

    def set_data(self, data) -> None:
        self._data = data

