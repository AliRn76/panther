
class APIException(Exception):
    detail: str | dict | list = 'server error'
    status_code: int = 500

    def __init__(self, detail=None, status_code=None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code


class UserNotFound(APIException):
    detail = 'not found'
    status_code = 403


class AuthenticationException(APIException):
    detail = 'authentication error'
    status_code = 401


class MissingSessionError(APIException):
    """
    Exception raised for when the user tries to access a database session before it is created.
    """
    detail = 'missing Session error'
    status_code = 402


class SessionNotInitialisedError(APIException):
    """
    Exception raised when the user creates a new DB session without first initialising it.
    """
    detail = 'Session not initialised!'
    status_code = 401
