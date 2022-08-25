from pydantic import BaseModel


class UserInputSerializer(BaseModel):
    id: int
    username: str
    password: str
    age: int


class UserOutputSerializer(BaseModel):
    id: int
    username: str
