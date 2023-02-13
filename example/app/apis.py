from datetime import timedelta

from app.models import User
from app.serializers import UserInputSerializer, UserOutputSerializer

from panther.app import API
from panther.db.connection import redis
from panther.logger import logger
from panther.request import Request
from panther.response import Response


@API(cache=False, cache_exp_time=timedelta(hours=1), auth=False)
async def return_none(request: Request):
    print(f'{request.user=}')
    return


@API()
async def return_dict():
    return {'detail': 'ok'}


@API()
async def return_list():
    return [1, 2, 3]


@API()
async def return_tuple():
    return 1, 2, 3, 4


@API()
async def return_response_none():
    return Response()


@API()
async def return_response_dict():
    return Response(data={'detail': 'ok'}, status_code=201)


@API()
async def return_response_list():
    return Response(data=['car', 'home', 'phone'], status_code=202)


@API()
async def return_response_tuple():
    return Response(data=('car', 'home', 'phone', 'book'), status_code=202)


@API(input_model=UserInputSerializer)
async def res_request_data(request: Request):
    return Response(data=request.data)


@API(input_model=UserInputSerializer, output_model=UserOutputSerializer)
async def res_request_data_with_output_model(request: Request):
    return Response(data=request.data)


@API(input_model=UserInputSerializer)
async def using_redis(request: Request):
    redis.set('ali', '1')
    logger.debug(f"{redis.get('ali') = }")
    return Response()


@API(input_model=UserInputSerializer)
async def using_sqlalchemy(request: Request):

    print(type(request.data))

    user = User.create_and_commit(username=request.data.username, password=request.data.password)
    print(f'{user = }')
    print(f'{user.username = }')
    print(f'{user.id = }')
    get_user = User.get_one(username='ali2', password='123')
    print(f'{get_user.id = }')
    return Response()


async def single_user(request: Request):
    # # print(f'{dir(request) = }')
    # print(f'{request.data = }')
    # # print(f'{request.query_params = }')
    #
    # user = User.create_and_commit(username='ali', password='123')
    # # print(f'{user = }')
    # # print(f'{user.username = }')
    #
    # redis.set('ali', '1')
    # logger.debug(f"{redis.get('ali') = }")
    #
    # get_user = User.get_one(username='ali', password='123')
    # # print(f'{get_user = }')
    #
    # get_users = User.list()
    # # for u in get_users:
    # #     print(f'{u.id = }')
    # #     print(f'{u.username = }')
    #
    # last_user = User.last()
    # # print(f'{last_user.id = }')
    #
    # # raise UserNotFound
    # a = [
    #     {
    #         'id': 1,
    #         'username': 'ali',
    #         'password': '111',
    #     },
    #     {
    #         'id': 2,
    #         'username': 'ali2',
    #         'password': '1112',
    #     },
    #     {
    #         'id': 3,
    #         'username': 'ali3',
    #         'password': '1113',
    #     }
    # ]
    # b = 'asdf'
    # c = {1, 2, 4}
    #
    # class A:
    #     ...
    # d = A()
    e = True
    # return Response(status_code=200, data=a)
    return Response(status_code=200)


# @API(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}

