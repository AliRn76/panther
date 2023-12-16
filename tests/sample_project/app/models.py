from panther.db.models import BaseUser


class User(BaseUser):
    age: int
