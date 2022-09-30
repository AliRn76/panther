from panther.db import BaseModel


class User(BaseModel):
    username: str
    password: str
