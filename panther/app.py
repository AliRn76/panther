from orjson.orjson import JSONDecodeError

from panther.db import BaseModel
from pydantic import ValidationError
from panther.request import Request
from panther.response import Response
from panther.exceptions import APIException


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
        if issubclass(type(data), BaseModel):
            _data = output_model(**data.dict()).dict()
        elif isinstance(data, dict):
            _data = output_model(**data).dict()
        elif isinstance(data, list) or isinstance(data, tuple):
            _data = [output_model(**d).dict() for d in data]
        elif isinstance(data, str) or isinstance(data, bool) or isinstance(data, set):
            raise TypeError('Type of Response data is not match with output_model. '
                            '\n*hint: You may want to pass None to output_model')
        else:
            raise TypeError(f"Type of Response 'data' is not valid.")
        return _data

    @classmethod
    def post(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
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
    def put(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
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
    def get(cls, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator

    @classmethod
    def delete(cls, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                if not isinstance(response, Response):
                    response = Response(data=response)
                data = cls.clean_output(data=response._data, output_model=output_model)
                response.set_data(data)
                return response
            return wrapper
        return decorator
