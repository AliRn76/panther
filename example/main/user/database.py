from framework.databases import Database, DBFields
from framework.databases import fields


class UserDB(Database):
    username = DBFields.Char(min_len=8, max_len=120, unique=True)
    email = DBFields.Email(max_len=120, unique=True)

    is_active = DBFields.Bool(default=True)
    is_admin = DBFields.Bool(default=False)

    password = DBFields.Password(hash_method='***')

    class Config:
        ...
