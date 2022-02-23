from framework.api import API
from framework.decorators import validation
from .serializer import UserInputSerializer, UserSerializer


@API(input=UserInputSerializer, output_model=UserSerializer)
def single_user(request, body):
    return {'detail': 'ok'}


@validation(input=UserInputSerializer, output=UserSerializer)
def single_user(request, body):
    body: UserInputSerializer
    return {'detail': 'ok'}
