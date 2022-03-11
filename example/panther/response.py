import orjson


class Response:
    def __init__(self, data: dict | list | str | bool, status_code: int = 200):
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
        if isinstance(self._data, dict) or isinstance(self._data, list) or isinstance(self._data, bool):
            return orjson.dumps(self._data)
        elif isinstance(self._data, str):
            return orjson.dumps({'detail': self._data})
        else:
            raise TypeError(f"Response 'data' Should Be dict or str. ('{self._data}' -> {type(self._data)})")

    def set_data(self, data: dict) -> None:
        self._data = data

