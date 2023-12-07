from pydantic import BaseModel, constr

from panther.file_handler import File, Image


class UserInputSerializer(BaseModel):
    username: str
    password: constr(min_length=8)


class UserOutputSerializer(BaseModel):
    username: str


class UserUpdateSerializer(BaseModel):
    username: str


class FileSerializer(BaseModel):
    name: str
    image: File
    age: int


class ImageSerializer(BaseModel):
    image: Image
