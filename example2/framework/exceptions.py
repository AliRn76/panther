
class APIException(Exception):
    pass


class JWTError(APIException):
    pass


class JWTClaimsError(APIException):
    pass


class ExpiredSignatureError(JWTError):
    pass


