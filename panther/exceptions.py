from panther import status


class PantherError(Exception):
    pass


class DatabaseError(Exception):
    pass


class BaseError(Exception):
    detail: str | dict | list = 'Internal Server Error'
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str | dict | list = None, status_code: int = None, headers: dict = None):
        self.detail = detail or self.detail
        self.status_code = status_code or self.status_code
        self.headers = headers


class APIError(BaseError):
    detail: str | dict | list = 'Internal Server Error'
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR


class WebsocketError(BaseError):
    detail: str | dict | list = 'Internal Error'
    status_code: int = status.WS_1011_INTERNAL_ERROR


class RedirectAPIError(APIError):
    def __init__(self, url: str, status_code: int = status.HTTP_302_FOUND):
        super().__init__(headers={'Location': url}, status_code=status_code)


class BadRequestAPIError(APIError):
    detail = 'Bad Request'
    status_code = status.HTTP_400_BAD_REQUEST


class AuthenticationAPIError(APIError):
    detail = 'Authentication Error'
    status_code = status.HTTP_401_UNAUTHORIZED


class AuthorizationAPIError(APIError):
    detail = 'Permission Denied'
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundAPIError(APIError):
    detail = 'Not Found'
    status_code = status.HTTP_404_NOT_FOUND


class MethodNotAllowedAPIError(APIError):
    detail = 'Method Not Allowed'
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED


class UnprocessableEntityError(APIError):
    detail = 'Unprocessable Entity Error'
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class UpgradeRequiredError(APIError):
    detail = 'This service requires use of the WebSocket protocol.'
    status_code = status.HTTP_426_UPGRADE_REQUIRED


class ThrottlingAPIError(APIError):
    detail = 'Too Many Request'
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class InvalidPathVariableAPIError(APIError):
    def __init__(self, value: str, variable_type: type):
        detail = f'Path variable `{value}` is not `{variable_type.__name__}`'
        super().__init__(detail=detail, status_code=status.HTTP_400_BAD_REQUEST)
