from app.models import User
from app.serializers import UserInputSerializer, UserOutputSerializer
from panther.logger import logger
from panther.response import Response
from panther.request import Request
from panther.app import API


@API.post(input_model=UserInputSerializer)
async def single_user(request: Request):
    # print(f'{request.data = }')
    user = User.create_and_commit(username='ali', password='123')
    # print(f'{user = }')
    # print(f'{user.username = }')
    get_user = User.list()
    # get_user = User.get_one(username='ali', password='123')
    print(f'{get_user = }')
    for u in get_user:
        print(f'{u.id = }')
        print(f'{u.username = }')

    last_user = User.last()
    # print(f'{dir(request) = }')
    # print(f'{request.query_params = }')
    # raise UserNotFound
    a = [
        {
            'id': 1,
            'username': 'ali',
            'password': '111',
        },
        {
            'id': 2,
            'username': 'ali2',
            'password': '1112',
        },
        {
            'id': 3,
            'username': 'ali3',
            'password': '1113',
        }
    ]
    b = 'asdf'
    c = {1, 2, 4}

    class A:
        ...
    d = A()
    e = True
    return Response(status_code=200, data=e)



# @API.post(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}

