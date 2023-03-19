from panther.db import Model


class User(Model):
    username: str
    password: str
