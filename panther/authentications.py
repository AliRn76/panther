from abc import abstractmethod
from datetime import datetime

from jose import JWTError, jwt

from panther.configs import config
from panther.db.models import BaseUser
from panther.exceptions import AuthenticationException
from panther.logger import logger
from panther.request import Request


class BaseAuthentication:
    @classmethod
    @abstractmethod
    def authentication(cls, request: Request):
        """
        Return User Instance
        """
        raise cls.exception(f'{cls.__name__}.authentication() is not implemented.')

    @staticmethod
    def exception(message: str, /):
        logger.error(f'Authentication Error: "{message}"')
        return AuthenticationException


class JWTAuthentication(BaseAuthentication):
    model = BaseUser
    keyword = 'Bearer'
    algorithm = 'HS256'
    HTTP_HEADER_ENCODING = 'iso-8859-1'  # Header encoding (see RFC5987)

    @classmethod
    def get_authorization_header(cls, request: Request):
        auth = request.headers.authorization

        if auth is None:
            raise cls.exception('Authorization is required')

        if isinstance(auth, str):
            auth = auth.encode(JWTAuthentication.HTTP_HEADER_ENCODING)
        return auth

    @classmethod
    def authentication(cls, request: Request):
        auth = cls.get_authorization_header(request).split()
        if not auth or auth[0].lower() != cls.keyword.lower().encode():
            raise cls.exception('Authorization keyword is not valid')
        if len(auth) != 2:
            raise cls.exception('Authorization should have 2 part')

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise cls.exception('Unicode Error')

        payload = cls.decode_jwt(token)
        return cls.get_user(payload)

    @classmethod
    def get_user(cls, payload: dict):
        """
        Get UserModel from config else use default UserModel from cls.model
        """
        if (user_id := payload.get('user_id')) is None:
            raise cls.exception('Payload does not have user_id')

        user_model = config['user_model'] or cls.model
        if user := user_model.find_one(id=user_id):
            return user

        raise cls.exception('User not found')

    @classmethod
    def encode_jwt(cls, user_id: int) -> str:
        """Encode JWT from user_id."""
        expire = datetime.utcnow() + config['jwt_config'].life_time
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'exp': expire,
        }
        return jwt.encode(access_payload, config['jwt_config'].key, algorithm=config['jwt_config'].algorithm)

    @classmethod
    def decode_jwt(cls, token: str) -> dict:
        """Decode JWT token to user_id (it can return multiple variable ... )"""
        try:
            return jwt.decode(
                token=token,
                key=config['jwt_config'].key,
                algorithms=[config['jwt_config'].algorithm],
            )
        except JWTError as e:
            raise cls.exception(e)

    @classmethod
    def login(cls, user_id: int) -> str:
        """Alias of encode_jwt()"""
        return cls.encode_jwt(user_id=user_id)

    @staticmethod
    def logout(user_id: int):
        # TODO:
        #   1. Save the token in cache
        #   2. Check logout cached token in authentication()
        pass

    @staticmethod
    def exception(message: str | JWTError, /):
        logger.error(f'JWT Authentication Error: "{message}"')
        return AuthenticationException

