from pydantic import Field

from panther import Panther, status
from panther.app import API
from panther.db import Model
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer


class User(Model):
    username: str
    password: str
    first_name: str = Field(default='', min_length=2)
    last_name: str = Field(default='', min_length=4)


class UserSerializer(metaclass=ModelSerializer, model=User):
    fields = ['username', 'first_name', 'last_name']
    # required_fields = ['first_name']


@API(input_model=UserSerializer)
async def model_serializer_example(request: Request):
    return Response(data=request.validated_data, status_code=status.HTTP_202_ACCEPTED)


url_routing = {
    '': model_serializer_example,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
