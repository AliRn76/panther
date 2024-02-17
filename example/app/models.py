from panther.db.models import BaseUser


class CustomQuery:
    @classmethod
    def find_last(cls):
        return cls.last()


class User(BaseUser, CustomQuery):
    username: str
    password: str
