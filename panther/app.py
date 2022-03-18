from pydantic import ValidationError
from panther.request import Request
from panther.exceptions import APIException


class API:

    @classmethod
    def validate_input(cls, data: dict, input_model):
        if input_model:
            try:
                input_model(**data)
            except ValidationError as validation_error:
                error = {}
                for e in validation_error.errors():
                    error[e['loc'][0]] = e['msg']
                raise APIException(status_code=400, detail=error)

    @classmethod
    def get(cls, output_model):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                _data = output_model(**response._data)
                response.set_data(_data.dict())
                return response
            return wrapper
        return decorator

    @classmethod
    def post(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                cls.validate_input(data=request.data, input_model=input_model)
                response = await func(request=request)
                _data = output_model(**response._data)
                response.set_data(_data.dict())
                return response
            return wrapper
        return decorator

    @classmethod
    def put(cls, input_model=None, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                request: Request = kwargs['request']
                cls.validate_input(data=request.data, input_model=input_model)
                response = await func(request=request)
                _data = output_model(**response._data)
                response.set_data(_data.dict())
                return response
            return wrapper
        return decorator

    @classmethod
    def delete(cls, output_model=None):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                _data = output_model(**response._data)
                response.set_data(_data.dict())
                return response
            return wrapper
        return decorator
