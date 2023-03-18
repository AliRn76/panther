from datetime import datetime
from panther.logger import logger
from panther.configs import config
from panther.db.models import User
from panther.request import Request
from panther.cli.utils import import_error
from panther.exceptions import AuthenticationException
try:
    from jose import JWTError, jwt
except ImportError:
    import_error('python-jose')
    exit()


class JWTAuthentication:
    model = User
    keyword = 'Bearer'
    algorithm = 'HS256'
    HTTP_HEADER_ENCODING = 'iso-8859-1'  # Header encoding (see RFC5987)

    @staticmethod
    def get_authorization_header(request: Request):
        auth = request.headers.authorization
        if isinstance(auth, str):
            auth = auth.encode(JWTAuthentication.HTTP_HEADER_ENCODING)
        return auth

    @classmethod
    def authentication(cls, request: Request):
        auth = cls.get_authorization_header(request).split()
        if not auth or auth[0].lower() != cls.keyword.lower().encode():
            logger.error(f'JWT Authentication Error: "token keyword is not valid"')
            raise AuthenticationException
        if len(auth) != 2:
            logger.error(f'JWT Authentication Error: "len of token should be 2"')
            raise AuthenticationException
        try:
            token = auth[1].decode()
        except UnicodeError:
            logger.error(f'JWT Authentication Error: "Unicode Error"')
            raise AuthenticationException

        payload = cls.decode_jwt(token)
        return cls.get_user(payload)

    @classmethod
    def get_user(cls, payload: dict):
        if (user_id := payload.get('user_id')) is None:
            logger.error(f'JWT Authentication Error: "Payload does not have user_id"')
            raise AuthenticationException

        user_model = config['user_model'] or cls.model
        if user := user_model.find_one(id=user_id):
            return user

        logger.error(f'JWT Authentication Error: "User not found"')
        raise AuthenticationException

    @staticmethod
    def encode_jwt(user_id: int) -> str:
        """Encode JWT from user_id."""
        expire = datetime.utcnow() + config['jwt_config'].life_time
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'exp': expire,
        }
        return jwt.encode(access_payload, config['jwt_config'].key, algorithm=config['jwt_config'].algorithm)

    @staticmethod
    def decode_jwt(token: str) -> dict:
        """Decode JWT token to user_id (it can return multiple variable ... )"""
        try:
            return jwt.decode(token, config['jwt_config'].key, algorithms=[config['jwt_config'].algorithm])
        except JWTError as e:
            logger.error(f'JWT Authentication Error: "{e}"')
            raise AuthenticationException

    @classmethod
    def login(cls, user_id: int) -> str:
        """alias of encode_jwt()"""
        return cls.encode_jwt(user_id=user_id)

    @staticmethod
    def logout(user_id: int):
        # TODO:
        #   1. Save the token in cache
        #   2. Check logout cached token in authentication()
        pass
