import time
from abc import abstractmethod
import logging
from typing import Literal

from jose import JWTError, jwt

from panther.configs import config
from panther.db.models import BaseUser, IDType, Model
from panther.exceptions import AuthenticationException
from panther.request import Request


logger = logging.getLogger('panther')


class BaseAuthentication:
    @classmethod
    @abstractmethod
    def authentication(cls, request: Request):
        """Return Instance of User"""
        msg = f'{cls.__name__}.authentication() is not implemented.'
        raise cls.exception(msg) from None

    @staticmethod
    def exception(message: str, /) -> type[AuthenticationException]:
        logger.error(f'Authentication Error: "{message}"')
        return AuthenticationException


class JWTAuthentication(BaseAuthentication):
    model = BaseUser
    keyword = 'Bearer'
    algorithm = 'HS256'
    HTTP_HEADER_ENCODING = 'iso-8859-1'  # Header encoding (see RFC5987)

    @classmethod
    def get_authorization_header(cls, request: Request) -> bytes:
        auth = request.headers.authorization

        if auth is None:
            msg = 'Authorization is required'
            raise cls.exception(msg) from None

        if isinstance(auth, str):
            auth = auth.encode(JWTAuthentication.HTTP_HEADER_ENCODING)
        return auth

    @classmethod
    def authentication(cls, request: Request) -> Model:
        auth = cls.get_authorization_header(request).split()
        if not auth or auth[0].lower() != cls.keyword.lower().encode():
            msg = 'Authorization keyword is not valid'
            raise cls.exception(msg) from None
        if len(auth) != 2:
            msg = 'Authorization should have 2 part'
            raise cls.exception(msg) from None

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = 'Unicode Error'
            raise cls.exception(msg) from None

        payload = cls.decode_jwt(token)
        return cls.get_user(payload)

    @classmethod
    def get_user(cls, payload: dict) -> Model:
        """Get UserModel from config, else use default UserModel from cls.model"""
        if (user_id := payload.get('user_id')) is None:
            msg = 'Payload does not have user_id'
            raise cls.exception(msg)

        user_model = config['user_model'] or cls.model
        if user := user_model.find_one(id=user_id):
            return user

        msg = 'User not found'
        raise cls.exception(msg) from None

    @classmethod
    def encode_jwt(cls, user_id: IDType, token_type: Literal['access', 'refresh'] = 'access') -> str:
        """Encode JWT from user_id."""
        issued_at = time.time()
        if token_type == 'access':
            expire = issued_at + config['jwt_config'].life_time
        else:
            expire = issued_at + config['jwt_config'].refresh_life_time

        claims = {
            'token_type': token_type,
            'user_id': user_id,
            'iat': issued_at,
            'exp': expire,
        }
        return jwt.encode(
            claims,
            key=config['jwt_config'].key,
            algorithm=config['jwt_config'].algorithm,
        )

    @classmethod
    def encode_refresh_token(cls, user_id: IDType) -> str:
        """Encode JWT from user_id."""
        return cls.encode_jwt(user_id=user_id, token_type='refresh')

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
            raise cls.exception(e) from None

    @classmethod
    def login(cls, user_id: IDType) -> str:
        """Alias of encode_jwt()"""
        return cls.encode_jwt(user_id=user_id)

    @staticmethod
    def exception(message: str | JWTError, /) -> type[AuthenticationException]:
        logger.error(f'JWT Authentication Error: "{message}"')
        return AuthenticationException
