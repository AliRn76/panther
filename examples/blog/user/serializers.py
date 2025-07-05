from panther.db.models import BaseUser
from panther.serializer import ModelSerializer


class UserSerializer(ModelSerializer):
    class Config:
        model = BaseUser
        fields = ['username', 'password']


class UserOutputSerializer(ModelSerializer):
    class Config:
        model = BaseUser
        fields = '*'
        exclude = ['password']
