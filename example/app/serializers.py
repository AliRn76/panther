from app.models import User
from pydantic import BaseModel, constr

from panther.file_handler import File, Image
from panther.serializer import ModelSerializer


class UserInputSerializer(BaseModel):
    username: str
    password: constr(min_length=8)


class UserOutputSerializer(BaseModel):
    username: str


class UserUpdateSerializer(metaclass=ModelSerializer, model=User):
    fields = ['username']
    required_fields = ['username']


class FileSerializer(BaseModel):
    name: str
    image: File
    age: int


class ImageSerializer(BaseModel):
    image: Image
