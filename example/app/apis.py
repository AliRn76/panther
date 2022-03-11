from app.serializers import UserInputSerializer, UserOutputSerializer
from panther.response import Response
from panther.request import Request
from panther.app import API


@API.post(input_model=UserInputSerializer, output_model=UserOutputSerializer)
async def single_user(request: Request):
    print(f'{request.data = }')
    # print(f'{dir(request) = }')
    # print(f'{request.query_params = }')
    # raise UserNotFound
    return Response(status_code=200, data=request.data)
    # return 200, {'detail': 'ok'}
    # return {'detail': 'ok'}


# @API.post(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}

