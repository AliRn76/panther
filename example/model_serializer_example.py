from pydantic import Field
from pydantic import field_validator

from panther.db import Model
from panther.serializer import ModelSerializer


class User(Model):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)


class UserSerializer(ModelSerializer):
    age: int = Field(default=20)
    is_male: bool

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        required_fields = ['first_name']

    @field_validator('username', mode='before')
    def validate_username(cls, username):
        print(f'{username=}')
        return username

    def ok(self):
        print('ok')


print(UserSerializer(username='alirn', first_name='Ali', last_name='RnRn', is_male=1))
# print(UserSerializer.validate_username)
