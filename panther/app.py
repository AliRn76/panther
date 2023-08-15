import functools
from datetime import datetime, timedelta

from orjson.orjson import JSONDecodeError
from pydantic import ValidationError

from panther import status
from panther._utils import is_function_async
from panther.caching import cache_key, get_cached_response_data, set_cache_response
from panther.configs import config
from panther.exceptions import (
    APIException,
    AuthorizationException,
    InvalidPathVariableException,
    JsonDecodeException,
    MethodNotAllowed,
    ThrottlingException,
)
from panther.logger import logger
from panther.request import Request
from panther.response import IterableDataTypes, Response
from panther.throttling import Throttling, throttling_storage
from panther.utils import round_datetime

__all__ = ('API', 'GenericAPI')


class API:
    def __init__(
            self,
            *,
            input_model=None,
            output_model=None,
            auth: bool = False,
            permissions: list | None = None,
            throttling: Throttling = None,
            cache: bool = False,
            cache_exp_time: timedelta | int | None = None,
    ):
        self.input_model = input_model
        self.output_model = output_model
        self.auth = auth
        self.permissions = permissions or []
        self.throttling = throttling
        self.cache = cache
        self.cache_exp_time = cache_exp_time
        self.request: Request | None = None

    def __call__(self, func):
        @functools.wraps(func)
        async def wrapper(request: Request, **path_variables):
            self.request: Request = request  # noqa: Non-self attribute could not be type hinted

            # 1. Authentication
            self.handle_authentications()

            # 2. Throttling
            self.handle_throttling()

            # 3. Permissions
            self.handle_permissions()

            # 4. Validate Input
            if self.request.method in ['POST', 'PUT', 'PATCH']:
                self.validate_input()

            # 5. Validate Path Variables
            self.validate_path_variables(func, path_variables)

            # 6. Get Cached Response
            if self.cache and self.request.method == 'GET':
                if cached := get_cached_response_data(request=self.request):
                    return Response(data=cached.data, status_code=cached.status_code)

            # 7. Put Request In kwargs (If User Wants It)
            kwargs = path_variables
            if req_arg := [k for k, v in func.__annotations__.items() if v == Request]:
                kwargs[req_arg[0]] = self.request

            # 8. Call Endpoint
            if is_function_async(func):
                response = await func(**kwargs)
            else:
                response = func(**kwargs)

            # 9. Clean Output
            if not isinstance(response, Response):
                response = Response(data=response)
            data = self.serialize_response_data(data=response._data)  # noqa: SLF001
            response.set_data(data)

            # 10. Set New Response To Cache
            if self.cache and self.request.method == 'GET':
                set_cache_response(request=self.request, response=response, cache_exp_time=self.cache_exp_time)

            # 11. Warning CacheExpTime
            if self.cache_exp_time and self.cache is False:
                logger.warning('"cache_exp_time" won\'t work while "cache" is False')

            return response

        return wrapper

    def handle_authentications(self) -> None:
        auth_class = config['authentication']
        if self.auth:
            if not auth_class:
                raise TypeError('"AUTHENTICATION" has not been set in core/configs')
            user = auth_class.authentication(self.request)
            self.request.set_user(user=user)

    def handle_throttling(self) -> None:
        if throttling := self.throttling or config['throttling']:
            key = cache_key(self.request)
            time = round_datetime(datetime.now(), throttling.duration)
            throttling_key = f'{time}-{key}'
            if throttling_storage[throttling_key] > throttling.rate:
                raise ThrottlingException

            throttling_storage[throttling_key] += 1

    def handle_permissions(self) -> None:
        for perm in self.permissions:
            if type(perm.authorization).__name__ != 'method':
                logger.error(f'{perm.__name__}.authorization should be "classmethod"')
                continue
            if perm.authorization(request=self.request) is False:
                raise AuthorizationException

    def validate_input(self):
        if self.input_model:
            try:
                validated_data = self.input_model(**self.request.pure_data)
                self.request.set_validated_data(validated_data)
            except ValidationError as validation_error:
                error = {e['loc'][0]: e['msg'] for e in validation_error.errors()}
                raise APIException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
            except JSONDecodeError:
                raise JsonDecodeException

    def serialize_response_data(self, data):
        """
        We serializer the response here instead of response.py file
        because we don't have access to the "output_model" there.
        """

        # None or Unchanged
        if data is None or self.output_model is None:
            return data

        return self.serialize_with_output_model(data)

    def serialize_with_output_model(self, data: any):
        # Dict
        if isinstance(data, dict):
            return self.output_model(**data).model_dump()

        # Iterable
        if isinstance(data, IterableDataTypes):
            return [self.serialize_with_output_model(d) for d in data]

        # Str | Bool
        raise TypeError('Type of Response data is not match with output_model. '
                        '\n*hint: You may want to pass None to output_model')

    @staticmethod
    def validate_path_variables(func, request_path_variables: dict):
        for name, value in request_path_variables.items():
            for variable_name, variable_type in func.__annotations__.items():
                if name == variable_name:
                    # Check the type and convert the value
                    if variable_type is bool:
                        request_path_variables[name] = value.lower() not in ['false', '0']

                    elif variable_type is int:
                        try:
                            request_path_variables[name] = int(value)
                        except ValueError:
                            raise InvalidPathVariableException(value=value, variable_type=variable_type)
                    break


class GenericAPI:
    input_model = None
    output_model = None
    auth: bool = False
    permissions: list | None = None
    throttling: Throttling = None
    cache: bool = False
    cache_exp_time: timedelta | int | None = None

    async def get(self, *args, **kwargs):
        raise MethodNotAllowed

    async def post(self, *args, **kwargs):
        raise MethodNotAllowed

    async def put(self, *args, **kwargs):
        raise MethodNotAllowed

    async def patch(self, *args, **kwargs):
        raise MethodNotAllowed

    async def delete(self, *args, **kwargs):
        raise MethodNotAllowed

    @classmethod
    async def call_method(cls, *args, **kwargs):
        match kwargs['request'].method:
            case 'GET':
                func = cls().get
            case 'POST':
                func = cls().post
            case 'PUT':
                func = cls().put
            case 'PATCH':
                func = cls().patch
            case 'DELETE':
                func = cls().delete

        return await API(
            input_model=cls.input_model,
            output_model=cls.output_model,
            auth=cls.auth,
            permissions=cls.permissions,
            throttling=cls.throttling,
            cache=cls.cache,
            cache_exp_time=cls.cache_exp_time,
        )(func)(*args, **kwargs)
