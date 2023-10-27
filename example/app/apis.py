import datetime
import time
from datetime import timedelta

from app.models import User
from app.serializers import FileSerializer, UserInputSerializer, UserOutputSerializer, UserUpdateSerializer
from core.permissions import UserPermission

from panther import status
from panther.app import API, GenericAPI
from panther.authentications import JWTAuthentication
from panther.background_tasks import background_tasks, BackgroundTask
from panther.db.connection import redis
from panther.logger import logger
from panther.request import Request
from panther.response import HTMLResponse, Response
from panther.throttling import Throttling
from panther.websocket import send_message_to_websocket, close_websocket_connection


class ReturnNone(GenericAPI):
    async def get(self, request: Request):
        return None


@API()
async def return_none():
    return None


@API(cache=True)
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
    print('ok')
    print(f'{request.data=}')
    print(f'{request.validated_data=}')
    return Response(data=request.validated_data, status_code=204)


@API(input_model=UserInputSerializer, output_model=UserOutputSerializer)
async def res_request_data_with_output_model(request: Request):
    return Response(data=request.validated_data)


@API(input_model=UserInputSerializer)
async def using_redis(request: Request):
    redis.set('ali', '1')
    logger.debug(f"{redis.get('ali') = }")
    return Response()


@API()
async def login():
    user = User.insert_one(username='Ali', password='xxxx')
    token = JWTAuthentication.encode_jwt(user.id)
    return Response(token)


@API(auth=True)
async def auth_true(request: Request):
    return Response(request.user)


@API(auth=True, permissions=[UserPermission])
async def check_permission(request: Request):
    return Response(request.user)


@API(throttling=Throttling(rate=5, duration=timedelta(minutes=1)))
async def rate_limit():
    return Response(data=('car', 'home', 'phone', 'book'), status_code=202)


@API(input_model=UserUpdateSerializer)
async def patch_user(request: Request):
    _, user = User.find_or_insert(username='Ali', password='1', age=12)
    user.update(**request.validated_data.model_dump())
    return Response(data=user)


class PatchUser(GenericAPI):
    input_model = UserUpdateSerializer

    def patch(self, request: Request, *args, **kwargs):
        _, user = User.find_or_insert(username='Ali', password='1', age=12)
        user.update(**request.validated_data.model_dump())
        return Response(data=user)


@API()
async def single_user(request: Request):
    # users = User.insert_one(username='Ali', password='1', age=12)
    # users = User.find(id="64bd711cd73aa4a30786db77")
    # print(f'{users=}')
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
    # e = True
    # return Response(status_code=200, data=a)
    return Response(status_code=200)


# @API(input=UserInputSerializer, output_model=UserSerializer)
def create_user(request, body):
    return {'detail': 'ok'}


class FileAPI(GenericAPI):
    input_model = FileSerializer

    def post(self, request: Request, *args, **kwargs):
        body: FileSerializer = request.validated_data
        with open(body.image.file_name, 'wb') as file:
            file.write(body.image.file)
        return {'detail': 'ok'}


class HTMLAPI(GenericAPI):
    def get(self, *args, **kwargs):
        html_data = """<!DOCTYPE html>
<html>
    <body>
        <h1>Hellow World</h1>
    </body>
</html>"""
        return HTMLResponse(data=html_data)


@API()
async def send_message_to_websocket_api(connection_id: str):
    await send_message_to_websocket(connection_id=connection_id, data='Hello From API')
    await close_websocket_connection(connection_id=connection_id, reason='ok')
    return Response(status_code=status.HTTP_202_ACCEPTED)


@API()
async def run_background_tasks_api():
    async def hello(name: str):
        time.sleep(5)
        print(f'Done {name}')
    task = (
        BackgroundTask(hello, 'ali1')
        .interval(2)
        .interval_wait(datetime.timedelta(seconds=2))
        # .on_time(datetime.time(hour=19, minute=18, second=10))
    )
    background_tasks.add_task(task)
    return Response()
