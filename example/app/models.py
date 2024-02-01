from panther.db.models import BaseUser


class User(BaseUser):
    username: str
    password: str
