from user.serializers import UserOutputSerializer, UserSerializer

from panther import status
from panther.app import GenericAPI
from panther.db.models import BaseUser
from panther.exceptions import BadRequestAPIError
from panther.request import Request
from panther.response import Response
from panther.utils import timezone_now


class RegisterAPI(GenericAPI):
    input_model = UserSerializer
    output_model = UserOutputSerializer

    async def post(self, request: Request, **kwargs):
        if await BaseUser.exists(username=request.validated_data.username):
            raise BadRequestAPIError(detail='User with this username already exists.')
        instance = await BaseUser.insert_one(
            username=request.validated_data.username,
            date_created=timezone_now(),
        )
        await instance.set_password(request.validated_data.password)
        return Response(data=instance, status_code=status.HTTP_201_CREATED)


class LoginAPI(GenericAPI):
    input_model = UserSerializer

    async def post(self, request: Request):
        user = await BaseUser.find_one_or_raise(username=request.validated_data.username)
        if not user.check_password(request.validated_data.password):
            raise BadRequestAPIError(detail={'detail': 'username or password was wrong.'})
        tokens = await user.login()
        return Response(data=tokens, status_code=status.HTTP_200_OK)
