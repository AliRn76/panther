from jose import JWTError, jwt
from datetime import datetime
from panther.configs import JWTConfig
from example.core.configs import JWTConfig
from panther.exceptions import CredentialsException


class JWTAuthentication:
    def __init__(self, token: str):
        self.token = token
        self.user_id = self.decode_jwt(token)

    def __str__(self):
        return f'Authentication(user_id={self.user_id}, token={self.token[:20]}...)'

    @staticmethod
    def encode_jwt(user_id: int) -> str:
        """ Encode JWT from user_id """
        expire = datetime.utcnow() + JWTConfig['TokenLifeTime']
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'exp': expire
        }
        return jwt.encode(access_payload, JWTConfig['Key'], algorithm=JWTConfig['Algorithm'])

    @staticmethod
    def decode_jwt(token: str) -> int:
        """ Decode JWT token to user_id (it can return multiple variable ... ) """
        try:
            payload = jwt.decode(token, JWTConfig['Key'], algorithms=[JWTConfig['Algorithm']])
            user_id: int = payload.get('user_id')
            if user_id is None:
                raise CredentialsException
        except JWTError:
            raise CredentialsException
        return user_id
