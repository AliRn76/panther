class BaseException:
    """ Base class Exception """
    pass


class HTTPException(BaseException):
    """ HTTP Error base Exception """
    pass


class IsNotHTTPError(HTTPException):
    """ for check HTTP method """
    pass


class APIException(BaseException):
    pass


class JWTError(APIException):
    pass


class JWTClaimsError(APIException):
    pass


class ExpiredSignatureError(JWTError):
    pass
