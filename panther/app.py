import functools
from datetime import timedelta

from pydantic import ValidationError
from orjson.orjson import JSONDecodeError

from panther.configs import config
from panther.logger import logger
from panther.request import Request
from panther.response import Response, IterableDataTypes
from panther.caching import get_cached_response_data, set_cache_response
from panther.exceptions import APIException, InvalidPathVariableException


class API:
    def __init__(
            self,
            input_model=None,
            output_model=None,
            auth: bool = False,
            cache: bool = False,
            cache_exp_time: timedelta | int | None = None,
    ):
        self.input_model = input_model
        self.output_model = output_model
        self.auth = auth
        self.cache = cache
        self.cache_exp_time = cache_exp_time or config['default_cache_exp']
        self.request: Request | None = None

    def __call__(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            self.request: Request = kwargs.pop('request')  # NOQA: Non-self attribute could not be type hinted

            # Handle Authentication
            self.handle_authentications()

            # Validate Input
            self.validate_input()

            # Validate Path Variables
            self.validate_path_variables(func, kwargs)

            # Get Cached Response
            if self.cache and self.request.method == 'GET':
                if cached := get_cached_response_data(request=self.request):
                    return Response(data=cached.data, status_code=cached.status_code)

            # Put Request In kwargs
            if req_arg := [k for k, v in func.__annotations__.items() if v == Request]:
                kwargs[req_arg[0]] = self.request

            # Call Endpoint
            response = await func(**kwargs)

            # Clean Output
            if not isinstance(response, Response):
                response = Response(data=response)
            data = self.serialize_response_data(data=response._data)
            response.set_data(data)

            # Set New Response To Cache
            if self.cache and self.request.method == 'GET':
                set_cache_response(request=self.request, response=response, cache_exp_time=self.cache_exp_time)

            # Warning CacheExpTime
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

    def validate_input(self):
        if self.input_model:
            try:
                validated_data = self.input_model(**self.request.pure_data)
                self.request.set_validated_data(validated_data)
            except ValidationError as validation_error:
                error = {e['loc'][0]: e['msg'] for e in validation_error.errors()}
                raise APIException(status_code=400, detail=error)
            except JSONDecodeError:
                raise APIException(status_code=400, detail={'detail': 'JSON Decode Error'})

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
