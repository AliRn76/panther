from panther.db import Column, String, Integer
from panther.db.models import MongoBaseModel, SQLBaseModel


# class User(SQLBaseModel):
#     __tablename__ = 'User'
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String)
#     password = Column(String)


class User(MongoBaseModel):
    username: str
    password: str
