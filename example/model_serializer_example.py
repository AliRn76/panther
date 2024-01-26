from pydantic import Field, field_validator, ConfigDict

from panther.db import Model
from panther.serializer import ModelSerializer


class User(Model):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)


class UserSerializer(ModelSerializer):
    """
    Hello this is doc
    """
    model_config = ConfigDict(str_to_upper=False)  # Has more priority
    age: int = Field(default=20)
    is_male: bool
    username: str

    class Config:
        str_to_upper = True
        model = User
        fields = ['username', 'first_name', 'last_name']
        required_fields = ['first_name']

    @field_validator('username', mode='before')
    def validate_username(cls, username):
        print(f'{username=}')
        return username


serialized = UserSerializer(username='alirn', first_name='Ali', last_name='RnRn', is_male=1)
# print(serialized.create())
