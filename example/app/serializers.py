from pydantic import BaseModel, constr


class UserInputSerializer(BaseModel):
    username: str
    password: constr(min_length=8)


class UserOutputSerializer(BaseModel):
    id: str
    username: str

