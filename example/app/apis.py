from app.serializers import UserInputSerializer, UserOutputSerializer
from framework.app import API
# from .serializer import UserInputSerializer, UserSerializer


# @API.get(output_model=UserSerializer)
from typing import Tuple, Union

from framework.response import Response


# async def single_user(request, body) -> Union[Tuple[int, dict], dict]:

@API.post(input_model=UserInputSerializer, output_model=UserOutputSerializer)
async def single_user(request) -> Response:
    print(f'{request.data = }')
    # print(f'{dir(request) = }')
    # print(f'{request.query_params = }')
    return Response(status_code=200, data=request.data)
    # return 200, {'detail': 'ok'}
    # return {'detail': 'ok'}


# @API.post(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}

