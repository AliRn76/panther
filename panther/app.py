import functools
from datetime import timedelta

from orjson.orjson import JSONDecodeError
from pydantic import ValidationError
from pydantic.main import BaseModel

from panther.caching import get_cached_response_data, set_cache_response
from panther.configs import config
from panther.exceptions import APIException, InvalidPathVariableException
from panther.logger import logger
from panther.request import Request
from panther.response import Response


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
        self.cache_exp_time = cache_exp_time
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
            data = self.clean_output(data=response._data)
            response.set_data(data)

            # Set New Response To Cache
            if self.cache and self.request.method == 'GET':
                if not (isinstance(self.cache_exp_time, timedelta) or isinstance(self.cache_exp_time, int)):
                    raise TypeError('cache_exp_time should be datetime.timedelta or int')
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
                raise TypeError('Authentication has not set in your configs.')
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

    def clean_output(self, data):
        # None
        if data is None or self.output_model is None:
            return data

        # Dict
        if isinstance(data, dict):
            _data = self.output_model(**data).dict()

        # BaseModel
        elif issubclass(type(data), BaseModel):
            _data = self.output_model(**data.dict()).dict()

        # List | Tuple
        elif isinstance(data, (list, tuple)):
            # Empty
            if len(data) == 0:
                return data

            # List | Tuple of BaseModel
            if isinstance(data[0], BaseModel):
                _data = [self.output_model(**d.dict()).dict() for d in data]

            # List | Tuple of Dict
            else:
                _data = [self.output_model(**d).dict() for d in data]

            # TODO: We didn't handle List | Tuple of List | Tuple | Bool | Str | ... (Recursive)

        # Str | Bool | Set
        elif isinstance(data, (str, bool, set)):
            raise TypeError('Type of Response data is not match with output_model. '
                            '\n*hint: You may want to pass None to output_model')

        # Unknown
        else:
            raise TypeError("Type of Response 'data' is not valid.")

        return _data

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
