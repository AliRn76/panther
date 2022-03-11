# from framework.app import API
# from .serializer import UserInputSerializer, UserSerializer


# @API.get(output_model=UserSerializer)
from typing import Tuple, Union


async def single_user(request, body) -> Union[Tuple[int, dict], dict]:
    return 200, {'detail': 'ok'}
    # return {'detail': 'ok'}


# @API.post(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}

