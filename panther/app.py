from datetime import timedelta
from pydantic.main import BaseModel
from pydantic import ValidationError
from orjson.orjson import JSONDecodeError

from panther.caching import get_cached_response_data, set_cache_response
from panther.exceptions import APIException
from panther.utils import import_class
from panther.response import Response
from panther.request import Request
from panther.configs import config
from panther.logger import logger


class API:

    @classmethod
    def validate_input(cls, request: Request, input_model):
        if input_model:
            try:
                validated_data = input_model(**request.data)
                request.set_data(validated_data)
            except ValidationError as validation_error:
                error = {e['loc'][0]: e['msg'] for e in validation_error.errors()}
                raise APIException(status_code=400, detail=error)
            except JSONDecodeError:
                raise APIException(status_code=400, detail={'detail': 'JSON Decode Error'})

    @classmethod
    def clean_output(cls, data, output_model):
        if data is None or output_model is None:
            return data
        if isinstance(data, dict):
            _data = output_model(**data).dict()
        elif issubclass(type(data), BaseModel):
            _data = output_model(**data.dict()).dict()
        elif isinstance(data, list) or isinstance(data, tuple):
            if len(data) == 0:
                return data
            if isinstance(data[0], BaseModel):
                _data = [output_model(**d.dict()).dict() for d in data]
            else:
                _data = [output_model(**d).dict() for d in data]
        elif isinstance(data, str) or isinstance(data, bool) or isinstance(data, set):
            raise TypeError('Type of Response data is not match with output_model. '
                            '\n*hint: You may want to pass None to output_model')
        else:
            raise TypeError(f"Type of Response 'data' is not valid.")
        return _data

    @classmethod
    def handle_authentications(cls, request: Request) -> None:
        if _auth_class := config['authentication']:
            auth_class = import_class(_auth_class)
            user = auth_class.authentication(request)
            request.set_user(user=user)

    @classmethod
    def post(cls, input_model=None, output_model=None, auth: bool = False):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                if auth:
                    cls.handle_authentications(request=request)

                cls.validate_input(request=request, input_model=input_model)
                response = await func(request) if Request in func.__annotations__.values() else await func()
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def put(cls, input_model=None, output_model=None, auth: bool = False):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                if auth:
                    cls.handle_authentications(request=request)
                cls.validate_input(request=request, input_model=input_model)
                response = await func(request) if Request in func.__annotations__.values() else await func()
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def get(cls, output_model=None, cache: bool = False, cache_exp_time: timedelta | int = None, auth: bool = False):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                if auth:
                    cls.handle_authentications(request=request)

                if cache:
                    if cached := get_cached_response_data(request=request):
                        return Response(data=cached.data, status_code=cached.status_code)

                response = await func(request) if Request in func.__annotations__.values() else await func()
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                if cache:
                    if not (isinstance(cache_exp_time, timedelta) or isinstance(cache_exp_time, int)):
                        raise TypeError('cache_exp_time should be datetime.timedelta or int')
                    set_cache_response(request=request, response=response, cache_exp_time=cache_exp_time)
                if cache_exp_time and cache is False:
                    logger.warning('"cache_exp_time" won\'t work while "cache" is False')
                return response
            return wrapper
        return decorator

    @classmethod
    def delete(cls, output_model=None, auth: bool = False):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                if auth:
                    cls.handle_authentications(request=request)
                response = await func(request) if Request in func.__annotations__.values() else await func()
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator
