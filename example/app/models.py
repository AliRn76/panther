from panther.db import BaseModel, Column, String, Integer


# class User(BaseModel):
#     __tablename__ = 'User'
#
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String)
#     password = Column(String)


class User(BaseModel):
    username: str
    password: str
