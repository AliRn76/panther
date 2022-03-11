from pydantic import BaseModel


class UserInputSerializer(BaseModel):
    id: int
    username: str
    password: str
