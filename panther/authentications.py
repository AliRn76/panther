try:
    from jose import JWTError, jwt
except ImportError:
    # TODO: Should we install the package ourselves?
    raise ImportError('Try to install python-jose with "pip install python-jose"')
from datetime import datetime

from panther.configs import config
from panther.db.models import User
from panther.exceptions import AuthenticationException
from panther.request import Request

JWTConfig = config['jwt_config']


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
            raise AuthenticationException

        if len(auth) != 2:
            raise AuthenticationException

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise AuthenticationException

        payload = cls.decode_jwt(token)
        return cls.get_user(payload)

    @classmethod
    def get_user(cls, payload: dict):
        if user_id := payload.get('user_id') is None:
            raise AuthenticationException
        user_model = config['user_model'] or cls.model
        user = user_model.get_one(id=user_id)
        if user is None:
            raise AuthenticationException
        return user

    @staticmethod
    def encode_jwt(user_id: int) -> str:
        """Encode JWT from user_id."""
        expire = datetime.utcnow() + JWTConfig.life_time
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'exp': expire,
        }
        return jwt.encode(access_payload, JWTConfig.key, algorithm=JWTConfig.algorithm)

    @staticmethod
    def decode_jwt(token: str) -> dict:
        """Decode JWT token to user_id (it can return multiple variable ... )"""
        try:
            return jwt.decode(token, JWTConfig.key, algorithms=[JWTConfig.algorithm])
        except JWTError:
            raise AuthenticationException
