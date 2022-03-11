from dataclasses import dataclass


class APIException(Exception):
    detail: str | dict | list = ''
    status_code: int = 400


class UserNotFound(APIException):
    detail: str = 'not found'
    status_code: int = 402
