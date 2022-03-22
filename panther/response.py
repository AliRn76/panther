import orjson


class Response:
    def __init__(self, data: dict | list | set  | tuple | str | bool, status_code: int = 200):
        """
        :param data: should be dict or str
        :param status_code: should be int
        """
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
        if isinstance(self._data, dict) or isinstance(self._data, list) or isinstance(self._data, tuple):
            return orjson.dumps(self._data)
        else:  # str, bool, set
            return orjson.dumps({'detail': self._data})

    def set_data(self, data: dict) -> None:
        self._data = data

