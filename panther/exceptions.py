from panther import status


class DBException(Exception):
    pass


class APIException(Exception):
    detail: str | dict | list = 'Internal Server Error'
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail=None, status_code=None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code


class MethodNotAllowed(APIException):
    detail = 'Method Not Allowed'
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED


class AuthenticationException(APIException):
    detail = 'Authentication Error'
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationException(APIException):
    detail = 'Permission Denied'
    status_code = status.HTTP_403_FORBIDDEN


class JsonDecodeException(APIException):
    detail = 'JSON Decode Error'
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class ThrottlingException(APIException):
    detail = 'Too Many Request'
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class InvalidPathVariableException(APIException):
    def __init__(self, value: str, variable_type: type):
        detail = f"Path variable '{value}' should be '{variable_type.__name__}'"
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)

