import functools
from datetime import timedelta, datetime

from pydantic import ValidationError
from orjson.orjson import JSONDecodeError

from panther import status
from panther.logger import logger
from panther.configs import config
from panther.request import Request
from panther.throttling import Throttling, throttling_storage
from panther.response import Response, IterableDataTypes
from panther.caching import get_cached_response_data, set_cache_response, cache_key
from panther.exceptions import APIException, InvalidPathVariableException, AuthorizationException, JsonDecodeException, \
    ThrottlingException
from panther.utils import round_datetime


class API:
    def __init__(
            self,
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
        async def wrapper(*args, **kwargs):
            self.request: Request = kwargs.pop('request')  # NOQA: Non-self attribute could not be type hinted

            # 1. Authentication
            self.handle_authentications()

            # 2. Throttling
            self.handle_throttling()

            # 3. Permissions
            self.handle_permissions()

            # 4. Validate Input
            self.validate_input()

            # 5. Validate Path Variables
            self.validate_path_variables(func, kwargs)

            # 6. Get Cached Response
            if self.cache and self.request.method == 'GET':
                if cached := get_cached_response_data(request=self.request):
                    return Response(data=cached.data, status_code=cached.status_code)

            # 7. Put Request In kwargs
            if req_arg := [k for k, v in func.__annotations__.items() if v == Request]:
                kwargs[req_arg[0]] = self.request

            # 8. Call Endpoint
            response = await func(**kwargs)

            # 9. Clean Output
            if not isinstance(response, Response):
                response = Response(data=response)
            data = self.serialize_response_data(data=response._data)  # NOQA: Access to a protected member
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
        because we don't have access to the "output_model" there
        """

        # None or Unchanged
        if data is None or self.output_model is None:
            return data

        return self.serialize_with_output_model(data)

    def serialize_with_output_model(self, data: any):
        # Dict
        if isinstance(data, dict):
            return self.output_model(**data).dict()

        # Iterable
        elif isinstance(data, IterableDataTypes):
            return [self.serialize_with_output_model(d) for d in data]

        # Str | Bool
        raise TypeError('Type of Response data is not match with output_model. '
                        '\n*hint: You may want to pass None to output_model')

    @staticmethod
    def validate_path_variables(func, variables):
        for user_var, value in variables.items():
            for func_var, _type in func.__annotations__.items():
                if user_var == func_var:
                    if _type is bool:
                        variables[user_var] = value.lower() not in ['false', '0']
                    elif _type is int:
                        try:
                            variables[user_var] = int(value)
                        except ValueError:
                            raise InvalidPathVariableException(value=value, arg_type=_type)
                    break
