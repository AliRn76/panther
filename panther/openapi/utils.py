import ast
import inspect

import pydantic

from panther import status
from panther.serializer import ModelSerializer


class EmptyResponseModel(pydantic.BaseModel):
    pass


class OutputSchema:
    """
    Its values only used in OpenAPI response schema
    """

    def __init__(
            self,
            model: type[ModelSerializer] | type[pydantic.BaseModel] = EmptyResponseModel,
            status_code: int = status.HTTP_200_OK,
    ):
        self.model = model
        self.status_code = status_code


class ParseEndpoint:
    """
    ParseEndpoint parses the endpoint (function-base/ class-base) and finds where it returns
        and extract the `data` and `status_code` values.
    """

    def __init__(self, endpoint, method):
        self.tree = ast.parse(inspect.getsource(endpoint))
        self.method = method

        self.status_code = status.HTTP_200_OK
        self.title = None
        self.data = {}

        self.parse()

    def parse(self):
        for branch in self.tree.body:
            match branch:
                case ast.ClassDef(name=name, body=body):
                    # class ...(GenericAPI):
                    #     def get(...
                    self.title = name
                    for part in body:
                        match part:
                            case ast.FunctionDef(name=name, body=function_body):
                                # def get(...
                                if name == self.method:
                                    self.parse_function(body=function_body)
                                    break
                            case ast.AsyncFunctionDef(name=name, body=function_body):
                                # async def get(...
                                if name == self.method:
                                    self.parse_function(body=function_body)
                                    break

                case ast.FunctionDef(name=name, body=body):
                    # def api(...
                    self.title = name
                    self.parse_function(body=body)

                case ast.AsyncFunctionDef(name=name, body=body):
                    # async def api(...
                    self.title = name
                    self.parse_function(body=body)

    def parse_function(self, body):
        for part in body:
            match part:
                case ast.Return(value=ast.Dict(keys=keys, values=values)):
                    # return {...}
                    self.status_code = 200
                    self.parse_dict_response(keys=keys, values=values)

                case ast.Return(value=ast.Name(id=name)):
                    # return my_data
                    self.status_code = 200
                    for value in self.searching_variable(body=body, name=name):
                        match value:
                            # my_data = {...}
                            case ast.Dict(keys=keys, values=values):
                                self.parse_dict_response(keys=keys, values=values)

                case ast.Return(value=ast.Call(args=args, keywords=keywords, func=func)):
                    if func.id == 'TemplateResponse':
                        return
                    # return Response(...
                    self.parse_response(body=body, args=args, keywords=keywords)

    def parse_dict_response(self, keys, values):
        for k, v in zip(keys, values):
            final_value = None
            match v:
                case ast.Constant(value=value):
                    final_value = value
            self.data[k.value] = final_value

    def parse_response(self, body, args, keywords):
        for keyword in keywords:
            if keyword.arg == 'data':
                self.parse_data(body=body, value=keyword.value)
            if keyword.arg == 'status_code':
                self.parse_status_code(body=body, value=keyword.value)

        for i, arg in enumerate(args):
            if i == 0:  # index 0 is `data`
                self.parse_data(body=body, value=arg)
            elif i == 1:  # index 1 is `status_code`
                self.parse_status_code(body=body, value=arg)

    def parse_status_code(self, body, value):
        match value:
            # return Response(?, status_code=my_status)
            # return Response(?, my_status)
            case ast.Name():
                for inner_value in self.searching_variable(body=body, name=value.id):
                    match inner_value:
                        # my_status = status.HTTP_202_ACCEPTED
                        case ast.Attribute(value=inner_inner_value, attr=attr):
                            if inner_inner_value.id == 'status':
                                self.status_code = getattr(status, attr)
                        # my_status = 202
                        case ast.Constant(value=inner_inner_value):
                            self.status_code = inner_inner_value

            # return Response(?, status_code=status.HTTP_202_ACCEPTED)
            # return Response(?, status.HTTP_202_ACCEPTED)
            case ast.Attribute(value=value, attr=attr):
                if value.id == 'status':
                    self.status_code = getattr(status, attr)
            # return Response(?, status_code=202)
            # return Response(?, 202)
            case ast.Constant(value=value):
                self.status_code = value

    def parse_data(self, body, value):
        match value:
            # return Response(data=my_data, ?)
            # return Response(my_data, ?)
            case ast.Name():
                for value in self.searching_variable(body=body, name=value.id):
                    match value:
                        # my_data = {...}
                        case ast.Dict(keys=keys, values=values):
                            self.parse_dict_response(keys=keys, values=values)

            # return Response(data={...}, ?)
            # return Response({...}, ?)
            case ast.Dict(keys=keys, values=values):
                self.parse_dict_response(keys=keys, values=values)

    def searching_variable(self, body, name):
        for part in body:
            match part:
                case ast.Assign(targets=targets, value=value):
                    for target in targets:
                        match target:
                            case ast.Name(id=inner_name):
                                if inner_name == name:
                                    yield value
