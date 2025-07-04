import logging
import time
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Literal

from panther.base_websocket import Websocket
from panther.cli.utils import import_error
from panther.configs import config
from panther.db.connections import redis
from panther.db.models import Model
from panther.exceptions import AuthenticationAPIError
from panther.request import Request
from panther.utils import generate_hash_value_from_string

try:
    from jose import JWTError, jwt
except ModuleNotFoundError as e:
    raise import_error(e, package='python-jose')

logger = logging.getLogger('panther')


class BaseAuthentication:
    @abstractmethod
    async def __call__(self, request: Request | Websocket):
        """Return Instance of User"""
        msg = f'{self.__class__.__name__}.__call__() is not implemented.'
        raise self.exception(msg) from None

    @classmethod
    def exception(cls, message: str | Exception, /) -> type[AuthenticationAPIError]:
        logger.error(f'{cls.__name__} Error: "{message}"')
        return AuthenticationAPIError


class JWTAuthentication(BaseAuthentication):
    """
    Retrieve the Authorization from header
    Example:
        Headers: {'authorization': 'Bearer the_jwt_token'}
    """

    model = None
    keyword = 'Bearer'
    algorithm = 'HS256'
    HTTP_HEADER_ENCODING = 'iso-8859-1'  # RFC5987

    async def __call__(self, request: Request | Websocket) -> Model | None:
        """Authenticate the user based on the JWT token in the Authorization header."""
        auth_header = self.get_authorization_header(request)
        # Set None as `request.user`
        if auth_header is None:
            return None

        token = self.get_token(auth_header=auth_header)
        if redis.is_connected and await self.is_token_revoked(token=token):
            msg = 'User logged out'
            raise self.exception(msg) from None
        payload = await self.decode_jwt(token)
        user = await self.get_user(payload)
        user._auth_token = token
        return user

    @classmethod
    def get_authorization_header(cls, request: Request | Websocket) -> list[str] | None:
        """Retrieve the Authorization header from the request."""
        if auth := request.headers.authorization:
            return auth.split()
        return None

    @classmethod
    def get_token(cls, auth_header):
        if len(auth_header) != 2:
            msg = 'Authorization header must contain 2 parts'
            raise cls.exception(msg) from None

        bearer, token = auth_header

        try:
            token.encode(JWTAuthentication.HTTP_HEADER_ENCODING)
        except UnicodeEncodeError as e:
            raise cls.exception(e) from None

        if bearer.lower() != cls.keyword.lower():
            msg = 'Authorization keyword is not valid'
            raise cls.exception(msg) from None

        return token

    @classmethod
    async def decode_jwt(cls, token: str) -> dict:
        """Decode a JWT token and return the payload."""
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
        """Fetch the user based on the decoded JWT payload from cls.model or config.UserModel"""
        if (user_id := payload.get('user_id')) is None:
            msg = 'Payload does not have `user_id`'
            raise cls.exception(msg)

        user_model = cls.model or config.USER_MODEL
        user = await user_model.find_one(id=user_id)
        if user is None:
            raise cls.exception('User not found')

        return user

    @classmethod
    def encode_jwt(cls, user_id: str, token_type: Literal['access', 'refresh'] = 'access') -> str:
        """Generate a JWT token for a given user ID."""
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
    async def login(cls, user) -> dict:
        """Generate access and refresh tokens for user login."""
        return {
            'access_token': cls.encode_jwt(user_id=user.id),
            'refresh_token': cls.encode_jwt(user_id=user.id, token_type='refresh'),
        }

    @classmethod
    async def logout(cls, user) -> None:
        """Log out a user by revoking their JWT token."""
        payload = await cls.decode_jwt(token=user._auth_token)
        await cls.revoke_token_in_cache(token=user._auth_token, exp=payload['exp'])

    @classmethod
    async def refresh(cls, user):
        if hasattr(user, '_auth_refresh_token'):
            # It happens in CookieJWTAuthentication
            token = user._auth_refresh_token
        else:
            token = user._auth_token

        payload = await cls.decode_jwt(token=token)

        if payload['token_type'] != 'refresh':
            raise cls.exception('Invalid token type; expected `refresh` token.')
        # Revoke after use
        await cls.revoke_token_in_cache(token=token, exp=payload['exp'])

        return await cls.login(user=user)

    @classmethod
    async def revoke_token_in_cache(cls, token: str, exp: int) -> None:
        """Mark the token as revoked in the cache."""
        if redis.is_connected:
            key = generate_hash_value_from_string(token)
            remaining_exp_time = int(exp - time.time())
            await redis.set(key, b'', ex=remaining_exp_time)
        else:
            logger.error('Redis is not connected; token revocation is not effective.')

    @classmethod
    async def is_token_revoked(cls, token: str) -> bool:
        """Check if the token is revoked by looking it up in the cache."""
        key = generate_hash_value_from_string(token)
        return bool(await redis.exists(key))


class QueryParamJWTAuthentication(JWTAuthentication):
    """
    Retrieve the Authorization from query params
    Example:
        https://example.com?authorization=the_jwt_without_bearer
    """

    @classmethod
    def get_authorization_header(cls, request: Request | Websocket) -> str | None:
        if 'authorization' in request.query_params:
            return request.query_params['authorization']
        return None

    @classmethod
    def get_token(cls, auth_header) -> str:
        return auth_header


class CookieJWTAuthentication(JWTAuthentication):
    """
    Retrieve the Authorization from cookies
    Example:
        Cookies: access_token=the_jwt_without_bearer
    """

    async def __call__(self, request: Request | Websocket) -> Model:
        user = await super().__call__(request=request)
        if refresh_token := request.headers.get_cookies().get('refresh_token'):
            # It's used in `cls.refresh()`
            user._auth_refresh_token = refresh_token
        return user

    @classmethod
    def get_authorization_header(cls, request: Request | Websocket) -> str | None:
        if token := request.headers.get_cookies().get('access_token'):
            return token
        return None

    @classmethod
    def get_token(cls, auth_header) -> str:
        return auth_header
