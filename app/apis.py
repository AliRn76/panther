from framework.api import API
from .serializer import UserInputSerializer, UserSerializer


@API(input_serializer=UserInputSerializer, output_serializer=UserSerializer)
def single_user(request, *args, **kwargs):
    return {'detail': 'ok'}


@input_validation(UserInputSerializer)
@output_serializer(UserSerializer)
def single_user(request, *args, **kwargs):
    return {'detail': 'ok'}
