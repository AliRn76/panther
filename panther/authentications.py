import logging
import time
from abc import abstractmethod
from datetime import timezone, datetime
from typing import Literal

from panther.base_websocket import Websocket
from panther.cli.utils import import_error
from panther.configs import config
from panther.db.connections import redis
from panther.db.models import BaseUser, Model
from panther.exceptions import AuthenticationAPIError
from panther.request import Request
from panther.utils import generate_hash_value_from_string

try:
    from jose import JWTError, jwt
except ModuleNotFoundError as e:
    raise import_error(e, package='python-jose')

logger = logging.getLogger('panther')


class BaseAuthentication:
    @classmethod
    @abstractmethod
    async def authentication(cls, request: Request | Websocket):
        """Return Instance of User"""
        msg = f'{cls.__name__}.authentication() is not implemented.'
        raise cls.exception(msg) from None

    @staticmethod
    def exception(message: str, /) -> type[AuthenticationAPIError]:
        logger.error(f'Authentication Error: "{message}"')
        return AuthenticationAPIError


class JWTAuthentication(BaseAuthentication):
    model = BaseUser
    keyword = 'Bearer'
    algorithm = 'HS256'
    HTTP_HEADER_ENCODING = 'iso-8859-1'  # RFC5987

    @classmethod
    def get_authorization_header(cls, request: Request | Websocket) -> str:
        if auth := request.headers.authorization:
            return auth
        msg = 'Authorization is required'
        raise cls.exception(msg) from None

    @classmethod
    async def authentication(cls, request: Request | Websocket) -> Model:
        auth_header = cls.get_authorization_header(request).split()

        if len(auth_header) != 2:
            msg = 'Authorization should have 2 part'
            raise cls.exception(msg) from None

        bearer, token = auth_header

        try:
            token.encode(JWTAuthentication.HTTP_HEADER_ENCODING)
        except UnicodeEncodeError as e:
            raise cls.exception(e) from None

        if bearer.lower() != cls.keyword.lower():
            msg = 'Authorization keyword is not valid'
            raise cls.exception(msg) from None

        if redis.is_connected and await cls._check_in_cache(token=token):
            msg = 'User logged out'
            raise cls.exception(msg) from None

        payload = cls.decode_jwt(token)
        user = await cls.get_user(payload)
        user._auth_token = token
        return user

    @classmethod
    def decode_jwt(cls, token: str) -> dict:
        """Decode JWT token to user_id (it can return multiple variable ... )"""
        try:
            return jwt.decode(
                token=token,
                key=config.JWT_CONFIG.key,
                algorithms=[config.JWT_CONFIG.algorithm],
            )
        except JWTError as e:
            raise cls.exception(e) from None

    @classmethod
    async def get_user(cls, payload: dict) -> Model:
        """Get UserModel from config, else use default UserModel from cls.model"""
        if (user_id := payload.get('user_id')) is None:
            msg = 'Payload does not have `user_id`'
            raise cls.exception(msg)

        user_model = config.USER_MODEL or cls.model
        if user := await user_model.find_one(id=user_id):
            return user

        msg = 'User not found'
        raise cls.exception(msg) from None

    @classmethod
    def encode_jwt(cls, user_id: str, token_type: Literal['access', 'refresh'] = 'access') -> str:
        """Encode JWT from user_id."""
        issued_at = datetime.now(timezone.utc).timestamp()
        if token_type == 'access':
            expire = issued_at + config.JWT_CONFIG.life_time
        else:
            expire = issued_at + config.JWT_CONFIG.refresh_life_time

        claims = {
            'token_type': token_type,
            'user_id': user_id,
            'iat': issued_at,
            'exp': expire,
        }
        return jwt.encode(
            claims,
            key=config.JWT_CONFIG.key,
            algorithm=config.JWT_CONFIG.algorithm,
        )

    @classmethod
    def login(cls, user_id: str) -> dict:
        """Return dict of access and refresh token"""
        return {
            'access_token': cls.encode_jwt(user_id=user_id),
            'refresh_token': cls.encode_jwt(user_id=user_id, token_type='refresh')
        }

    @classmethod
    async def logout(cls, raw_token: str) -> None:
        *_, token = raw_token.split()
        if redis.is_connected:
            payload = cls.decode_jwt(token=token)
            remaining_exp_time = payload['exp'] - time.time()
            await cls._set_in_cache(token=token, exp=int(remaining_exp_time))
        else:
            logger.error('`redis` middleware is required for `logout()`')

    @classmethod
    async def _set_in_cache(cls, token: str, exp: int) -> None:
        key = generate_hash_value_from_string(token)
        await redis.set(key, b'', ex=exp)

    @classmethod
    async def _check_in_cache(cls, token: str) -> bool:
        key = generate_hash_value_from_string(token)
        return bool(await redis.exists(key))

    @staticmethod
    def exception(message: str | JWTError | UnicodeEncodeError, /) -> type[AuthenticationAPIError]:
        logger.error(f'JWT Authentication Error: "{message}"')
        return AuthenticationAPIError


class QueryParamJWTAuthentication(JWTAuthentication):
    @classmethod
    def get_authorization_header(cls, request: Request | Websocket) -> str:
        if auth := request.query_params.get('authorization'):
            return auth
        msg = 'Authorization is required'
        raise cls.exception(msg) from None
