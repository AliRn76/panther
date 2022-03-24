from dataclasses import dataclass


@dataclass
class APIException(Exception):
    detail: str | dict | list = ''
    status_code: int = 400


class UserNotFound(APIException):
    detail: str = 'not found'
    status_code: int = 403


class MissingSessionError(APIException):
    """
    Exception raised for when the user tries to access a database session before it is created.
    """
    detail = "MissingSessionError"
    status_code = 402


class SessionNotInitialisedError(APIException):
    """
    Exception raised when the user creates a new DB session without first initialising it.
    """
    detail = "Session not initialised!"
    status_code = 401
