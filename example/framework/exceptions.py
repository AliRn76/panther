from dataclasses import dataclass


@dataclass
class APIException(BaseException):
    detail: str | dict | list
    status_code: int = 400
