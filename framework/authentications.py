from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import timedelta, datetime

from database import r
from models import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from exceptions import credentials_exception


class JWTAuthentication:
    def __init__(self, token: str):
        self.token = token
        self.user_id = self.decode_jwt(token)

    def __str__(self):
        return f'Authentication(user_id={self.user_id}, token={self.token[:20]}...)'

    @staticmethod
    def encode_jwt(user_id: int) -> str:
        """ Encode JWT from user_id """
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_payload = {
            'token_type': 'access',
            'user_id': user_id,
            'exp': expire
        }
        return jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_jwt(token: str) -> int:
        """ Decode JWT token to user_id (it can return multiple variable ... ) """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get('user_id')
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return user_id

    def find_jwt_in_db(self):
        """ Search for JWT in Main DB """
        q = self.db.query(User).filter_by(token=self.token).first()
        if q is not None:
            self._set_token_in_redis()
        return q is not None

    def _set_token_in_redis(self):
        r.set(name=self.token, value=1)

