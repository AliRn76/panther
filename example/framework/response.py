import orjson
from framework.logger import logger

class Response:
    def __init__(self, data: dict, status_code: int = 200):
        """
        :param data: should be dict or str
        :param status_code: should be int
        """
        self._status_code = status_code
        self._data = data
        # TODO: Add Header To Response

    @property
    def status_code(self):
        if isinstance(self._status_code, int):
            return self._status_code
        else:
            raise TypeError(f"Response 'status_code' Should Be int. ('{self._status_code}' -> {type(self._status_code)})")

    @property
    def data(self):
        if isinstance(self._data, dict):
            return orjson.dumps(self._data)
        elif isinstance(self._data, str):
            return orjson.dumps({'detail': self._data})
        else:
            raise TypeError(f"Response 'data' Should Be dict or str. ('{self._data}' -> {type(self._data)})")
