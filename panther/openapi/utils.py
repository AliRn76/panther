import ast
import inspect
import inspect as pyinspect
import types

from panther import status
from panther.app import GenericAPI
from panther.configs import config


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
                            # TODO: Can be list, int, bool, set, tuple, BaseModel, Model, ...

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


class OpenAPI:
    @classmethod
    def get_model_name(cls, model: type) -> str:
        if hasattr(model, '__name__'):
            return model.__name__
        return model.__class__.__name__

    @classmethod
    def extract_parameters_from_signature(cls, endpoint, method: str) -> list:
        params = []
        sig = None
        if isinstance(endpoint, types.FunctionType):
            sig = pyinspect.signature(endpoint)
        else:
            func = getattr(endpoint, method, None)
            if func:
                sig = pyinspect.signature(func)
        if not sig:
            return params
        for name, param in sig.parameters.items():
            if name in ('self', 'request'):
                continue
            # TODO: Get this value from FLAT_URLS, function can have *args or **kwargs ...
            param_schema = {'name': name, 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
            if param.annotation is int:
                param_schema['schema']['type'] = 'integer'
            elif param.annotation is bool:
                param_schema['schema']['type'] = 'boolean'
            elif param.annotation is float:
                param_schema['schema']['type'] = 'number'
            params.append(param_schema)
        return params

    @classmethod
    def parse_docstring(cls, docstring: str) -> tuple[str, str]:
        """Use first line as summary and rest of them as description"""
        if not docstring:
            return '', ''
        lines = docstring.strip().split('\n')
        summary = lines[0]
        description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ''
        return summary, description

    @classmethod
    def get_field_constraints(cls, field):
        # Extract constraints from Pydantic FieldInfo
        constraints = {}
        for attr in ['min_length', 'max_length', 'regex', 'ge', 'le', 'gt', 'lt']:
            value = getattr(field, attr, None)
            if value is not None:
                constraints[attr] = value
        return constraints

    @classmethod
    def enrich_schema_with_constraints(cls, schema, model):
        # Add field constraints to OpenAPI schema
        for name, field in model.model_fields.items():
            if 'properties' in schema and name in schema['properties']:
                schema['properties'][name].update(cls.get_field_constraints(field))
        return schema

    @classmethod
    def extract_content(cls, endpoint, http_method, schemas):
        if endpoint.output_schema and endpoint.output_schema.exclude_in_docs:
            return {}
        parsed = ParseEndpoint(endpoint=endpoint, method=http_method)
        responses = {}
        request_body = {}
        parameters = cls.extract_parameters_from_signature(endpoint, http_method)
        operation_id = f'{parsed.title}_{http_method}'
        if endpoint.output_schema and endpoint.output_schema.tags:
            tags = endpoint.output_schema.tags
        else:
            tags = [parsed.title] if parsed.title else [endpoint.__module__]
        summary, description = cls.parse_docstring(docstring=endpoint.__doc__)
        # Permissions, throttling, cache, middlewares
        x_permissions = [p.__name__ for p in endpoint.permissions] if endpoint.permissions else None

        x_throttling = None
        if endpoint.throttling:
            x_throttling = f'{endpoint.throttling.rate} per {endpoint.throttling.duration}'

        x_cache = None
        if endpoint.cache:
            x_cache = str(endpoint.cache)

        x_middlewares = None
        if endpoint.middlewares:
            x_middlewares = [getattr(m, '__name__', str(m)) for m in endpoint.middlewares]

        deprecated = False
        if endpoint.output_schema:
            deprecated = endpoint.output_schema.deprecated

        # Handle response schema
        if endpoint.output_schema:
            status_code = endpoint.output_schema.status_code
            model = endpoint.output_schema.model
            model_name = cls.get_model_name(model)
            if model_name not in schemas:
                schema = model.schema(ref_template='#/components/schemas/{model}')
                schema = cls.enrich_schema_with_constraints(schema, model)
                schemas[model_name] = schema
            schema_ref = {'$ref': f'#/components/schemas/{model_name}'}
        elif endpoint.output_model:
            status_code = parsed.status_code
            model = endpoint.output_model
            model_name = cls.get_model_name(model)
            if model_name not in schemas:
                schema = model.schema(ref_template='#/components/schemas/{model}')
                schema = cls.enrich_schema_with_constraints(schema, model)
                schemas[model_name] = schema
            schema_ref = {'$ref': f'#/components/schemas/{model_name}'}
        else:
            status_code = parsed.status_code
            schema_ref = {'properties': {k: {'default': v} for k, v in parsed.data.items()}}
        if schema_ref:
            responses = {'responses': {status_code: {'content': {'application/json': {'schema': schema_ref}}}}}
        # Add standard error responses
        error_responses = {}
        if endpoint.auth:
            error_responses[401] = {'description': 'Unauthorized'}
        if endpoint.permissions:
            error_responses[403] = {'description': 'Forbidden'}
        if endpoint.input_model:
            error_responses[400] = {'description': 'Bad Request'}
            error_responses[422] = {'description': 'Unprocessable Entity'}
        if error_responses:
            if 'responses' not in responses:
                responses['responses'] = {}
            responses['responses'] |= error_responses

        # Handle request body
        if endpoint.input_model and http_method in ['post', 'put', 'patch']:
            model = endpoint.input_model
            model_name = cls.get_model_name(model)
            if model_name not in schemas:
                schema = model.schema(ref_template='#/components/schemas/{model}')
                schema = cls.enrich_schema_with_constraints(schema, model)
                schemas[model_name] = schema
            request_body = {
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {'schema': {'$ref': f'#/components/schemas/{model_name}'}},
                    },
                },
            }
        # Add security (empty for public endpoints)
        security = [{'BearerAuth': []}] if endpoint.auth else []
        if x_permissions:
            description += f'<br>Permissions: {x_permissions}'
        if x_throttling:
            description += f'<br>Throttling: {x_throttling}'
        if x_cache:
            description += f'<br>Cache: {x_cache}'
        if x_middlewares:
            description += f'<br>Middlewares: {x_middlewares}'

        content = {
            'operationId': operation_id,
            'summary': summary,
            'description': description,
            'tags': tags,
            'parameters': parameters,
            'security': security,
            'deprecated': deprecated,
        }

        content |= responses
        content |= request_body
        return {http_method: content}

    @classmethod
    def get_content(cls):

        paths = {}
        schemas = {}

        for url, endpoint in config.FLAT_URLS.items():
            if not url.startswith('/'):
                url = f'/{url}'
            paths[url] = {}
            if isinstance(endpoint, types.FunctionType):
                for method in ['post', 'get', 'put', 'patch', 'delete']:
                    if method.upper() in endpoint.methods:
                        paths[url] |= cls.extract_content(endpoint, method, schemas)
            else:
                for method in ['post', 'get', 'put', 'patch', 'delete']:
                    # endpoint.post is not GenericAPI.post --> Method has overridden.
                    if getattr(endpoint, method) is not getattr(GenericAPI, method):
                        paths[url] |= cls.extract_content(endpoint, method, schemas)
        # Security Schemes
        security_schemes = {
            'BearerAuth': {  # TODO: extract this method from config.Authentication
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            },
        }
        openapi = {
            'openapi': '3.0.0',
            'info': {
                'title': 'Panther API',
                'version': '1.0.0',
                'description': 'Auto-generated OpenAPI documentation for Panther project.',
            },
            'paths': paths,
            'components': {'schemas': schemas, 'securitySchemes': security_schemes},
            'security': [{'BearerAuth': []}],
        }
        return openapi
