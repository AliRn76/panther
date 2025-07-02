"""
OpenAPI utilities for parsing endpoints and generating OpenAPI documentation.

This module provides classes and functions for analyzing Python endpoints
and generating OpenAPI 3.0 specification documents.
"""

import ast
import inspect
import logging
import types
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from panther import status
from panther.app import GenericAPI
from panther.configs import config

logger = logging.getLogger('panther')


class EndpointParser:
    """
    Parses endpoint functions and classes to extract response data and status codes.

    This class analyzes the AST (Abstract Syntax Tree) of endpoint functions
    to determine what data they return and what HTTP status codes they use.
    """

    def __init__(self, endpoint: Any, http_method: str):
        self.ast_tree = ast.parse(inspect.getsource(endpoint))
        self.http_method = http_method

        # Default values
        self.status_code = status.HTTP_200_OK
        self.endpoint_name = None
        self.response_data = {}

        self._parse_ast()

    def _parse_ast(self) -> None:
        """Parse the AST to extract endpoint information."""
        for node in self.ast_tree.body:
            match node:
                case ast.ClassDef(name=class_name, body=class_body):
                    # Handle class-based endpoints
                    # class ...(GenericAPI):
                    #     def get(self, ...
                    self.endpoint_name = class_name
                    self._parse_class_methods(class_body)

                case ast.FunctionDef(name=func_name, body=func_body):
                    # Handle function-based endpoints
                    # def api(...
                    self.endpoint_name = func_name
                    self._parse_function_body(func_body)

                case ast.AsyncFunctionDef(name=func_name, body=func_body):
                    # Handle async function-based endpoints
                    # async def api(...
                    self.endpoint_name = func_name
                    self._parse_function_body(func_body)

    def _parse_class_methods(self, class_body: list[ast.stmt]) -> None:
        """Parse methods within a class-based endpoint."""
        for node in class_body:
            match node:
                case ast.FunctionDef(name=method_name, body=method_body):
                    # def get(self, ...
                    if method_name == self.http_method:
                        self._parse_function_body(method_body)
                        break

                case ast.AsyncFunctionDef(name=method_name, body=method_body):
                    # async def get(self, ...
                    if method_name == self.http_method:
                        self._parse_function_body(method_body)
                        break

    def _parse_function_body(self, function_body: list[ast.stmt]) -> None:
        """Parse the body of a function to extract return statements."""
        for node in function_body:
            match node:
                case ast.Return(value=ast.Dict(keys=dict_keys, values=dict_values)):
                    # return {...}
                    self.status_code = status.HTTP_200_OK
                    self.response_data = self._extract_dict_data(dict_keys, dict_values)

                case ast.Return(value=ast.Name(id=variable_name)):
                    # return variable_name
                    self._extract_variable_data(function_body, variable_name)

                case ast.Return(value=ast.Call(args=call_args, keywords=call_keywords, func=func)):
                    # return Response(...)
                    self._parse_call(function_body=function_body, args=call_args, keywords=call_keywords, func=func)

    def _extract_dict_data(self, keys: list[ast.expr], values: list[ast.expr]) -> dict:
        """Extract data from a dictionary return statement."""
        response = {}
        for key, value in zip(keys, values):
            extracted_value = None
            match value:
                case ast.Constant(value=constant_value):
                    extracted_value = constant_value
            if hasattr(key, 'value'):
                response[key.value] = extracted_value
        return response

    def _extract_variable_data(self, function_body: list[ast.stmt], variable_name: str) -> None:
        """Extract data from a variable that contains a dictionary."""
        for variable_value in self._find_variable_assignments(function_body, variable_name):
            match variable_value:
                case ast.Dict(keys=dict_keys, values=dict_values):
                    # my_response = {...}
                    self.status_code = status.HTTP_200_OK
                    self.response_data = self._extract_dict_data(dict_keys, dict_values)
                case ast.List(elts=list_items):
                    # my_response = ['1', '2']
                    self.status_code = status.HTTP_200_OK
                    self.response_data = []
                    for item in list_items:
                        match item:
                            case ast.Constant(value=constant_value):
                                self.response_data.append(constant_value)
                case ast.Constant(value=constant_value):
                    # my_response = 'Hello World!'
                    self.response_data = constant_value
                case ast.Tuple(elts=tuple_items):
                    # my_response = (1, 2)
                    self.status_code = status.HTTP_200_OK
                    self.response_data = []
                    for item in tuple_items:
                        match item:
                            case ast.Constant(value=constant_value):
                                self.response_data.append(constant_value)
                case ast.Call(args=call_args, keywords=call_keywords, func=func):
                    self._parse_call(function_body=function_body, args=call_args, keywords=call_keywords, func=func)
                case _:
                    breakpoint()

    def _parse_call(self, function_body: list[ast.stmt], args: list[ast.expr], keywords: list[ast.keyword], func):
        if func.id == 'Response':
            self._parse_response_call(function_body=function_body, args=args, keywords=keywords)
        else:  # We assume this is subclass of BaseModel
            self.status_code = status.HTTP_200_OK
            for keyword in keywords:
                match keyword.value:
                    case ast.Constant(value=constant_value):
                        # CustomBaseModel(something='Hi')
                        self.response_data[keyword.arg] = constant_value
                    case ast.List(elts=list_items):
                        # CustomBaseModel(something=['1', '2'])
                        self.response_data[keyword.arg] = []
                        for item in list_items:
                            match item:
                                case ast.Constant(value=constant_value):
                                    self.response_data[keyword.arg].append(constant_value)
                    case ast.Dict(keys=dict_keys, values=dict_values):
                        # CustomBaseModel(something={...})
                        self.response_data[keyword.arg] = self._extract_dict_data(keys=dict_keys, values=dict_values)
                    case _:
                        logger.warning(f'Schema does not supported yet: {{{keyword.arg}: {keyword.value}}}')

    def _parse_response_call(
        self, function_body: list[ast.stmt], args: list[ast.expr], keywords: list[ast.keyword]
    ) -> None:
        """Parse Response() function calls."""
        # Handle keyword arguments
        for keyword in keywords:
            if keyword.arg == 'data':
                self._parse_data_argument(function_body, keyword.value)
            elif keyword.arg == 'status_code':
                self._parse_status_code_argument(function_body, keyword.value)

        # Handle positional arguments
        for index, arg in enumerate(args):
            if index == 0:  # First argument is data
                self._parse_data_argument(function_body=function_body, value=arg)
            elif index == 1:  # Second argument is status_code
                self._parse_status_code_argument(function_body=function_body, value=arg)

    def _parse_status_code_argument(self, function_body: list[ast.stmt], value: ast.expr) -> None:
        """Parse status code from various AST patterns."""
        match value:
            # return Response(?, status_code=my_status)
            # return Response(?, my_status)
            case ast.Name(id=variable_name):
                for variable_value in self._find_variable_assignments(function_body, variable_name):
                    self._extract_status_code_from_value(variable_value)

            # return Response(?, status_code=status.HTTP_202_ACCEPTED)
            # return Response(?, status.HTTP_202_ACCEPTED)
            case ast.Attribute(value=ast.Name(id=module_name), attr=attribute_name):
                # Handle: my_status = status.HTTP_202_ACCEPTED
                if module_name == 'status':
                    self.status_code = getattr(status, attribute_name)

            # return Response(?, status_code=202)
            # return Response(?, 202)
            case ast.Constant(value=constant_value):
                # Handle: my_status = 202
                self.status_code = constant_value

    def _parse_data_argument(self, function_body: list[ast.stmt], value: ast.expr) -> None:
        """Parse data argument from various AST patterns."""
        match value:
            # return Response(data=my_data, ?)
            # return Response(my_data, ?)
            case ast.Name(id=variable_name):
                # Handle: data=variable_name
                for variable_value in self._find_variable_assignments(function_body, variable_name):
                    match variable_value:
                        # my_data = {...}
                        case ast.Dict(keys=dict_keys, values=dict_values):
                            self.response_data = self._extract_dict_data(dict_keys, dict_values)

            # return Response(data={...}, ?)
            # return Response({...}, ?)
            case ast.Dict(keys=dict_keys, values=dict_values):
                # Handle: data={...}
                self.response_data = self._extract_dict_data(dict_keys, dict_values)

    def _extract_status_code_from_value(self, value: ast.expr) -> None:
        """Extract status code from a variable assignment value."""
        match value:
            case ast.Attribute(value=ast.Name(id=module_name), attr=attribute_name):
                # my_status = status.HTTP_202_ACCEPTED
                if module_name == 'status':
                    self.status_code = getattr(status, attribute_name)
            case ast.Constant(value=constant_value):
                # my_status = 202
                self.status_code = constant_value

    def _find_variable_assignments(self, function_body: list[ast.stmt], variable_name: str):
        """Find all assignments to a specific variable name."""
        for node in function_body:
            match node:
                case ast.Assign(targets=targets, value=value):
                    for target in targets:
                        match target:
                            case ast.Name(id=target_name):
                                if target_name == variable_name:
                                    yield value


class OpenAPIGenerator:
    """
    Generates OpenAPI 3.0 specification documents from Panther endpoints.

    This class analyzes registered endpoints and generates comprehensive
    OpenAPI documentation including schemas, paths, and security definitions.
    """

    HTTP_METHODS = ['post', 'get', 'put', 'patch', 'delete']
    REQUEST_BODY_METHODS = ['post', 'put', 'patch']

    @classmethod
    def get_model_name(cls, model: type[BaseModel]) -> str:
        """Get the name of a model class."""
        if hasattr(model, '__name__'):
            return model.__name__
        return model.__class__.__name__

    @classmethod
    def extract_path_parameters(cls, endpoint: Any, endpoint_name: str, http_method: str) -> list[dict[str, Any]]:
        """
        Extract path parameters from endpoint function signature.

        Args:
            endpoint: The endpoint function or class
            endpoint_name: Name of the endpoint function or class
            http_method: The HTTP method

        Returns:
            List of parameter schemas for OpenAPI
        """
        param_names = []
        for url, endpoint in config.FLAT_URLS.items():
            if endpoint.__name__ == endpoint_name:
                for part in url.split('/'):
                    if part.startswith('<'):
                        param_names.append(part.strip('< >'))
        if not param_names:
            return []

        signature = cls._get_function_signature(endpoint, http_method)
        parameters = []
        for param_name in param_names:
            if param_name not in signature.parameters:
                parameters.append({'name': param_name, 'in': 'path', 'required': True, 'schema': {'type': 'string'}})
            else:
                param_schema = cls._create_parameter_schema(param_name, signature.parameters[param_name])
                parameters.append(param_schema)

        return parameters

    @classmethod
    def _get_function_signature(cls, endpoint: Any, http_method: str):
        """Get the function signature for an endpoint."""
        if isinstance(endpoint, types.FunctionType):
            func = endpoint
        else:
            func = getattr(endpoint, http_method)
        return inspect.signature(obj=func)

    @classmethod
    def _create_parameter_schema(cls, param_name: str, param_info: inspect.Parameter) -> dict[str, Any]:
        """Create OpenAPI parameter schema from function parameter."""
        param_schema = {'name': param_name, 'in': 'path', 'required': True, 'schema': {'type': 'string'}}

        # Map Python types to OpenAPI types
        if param_info.annotation is int:
            param_schema['schema']['type'] = 'integer'
        elif param_info.annotation is bool:
            param_schema['schema']['type'] = 'boolean'
        elif param_info.annotation is float:
            param_schema['schema']['type'] = 'number'

        return param_schema

    @classmethod
    def parse_docstring(cls, docstring: str) -> tuple[str, str]:
        """Parse docstring into summary and description."""
        if not docstring:
            return '', ''

        lines = docstring.strip().split('\n')
        summary = lines[0]
        description = '<br>'.join(lines[1:]).strip() if len(lines) > 1 else ''

        return summary, description

    @classmethod
    def extract_field_constraints(cls, field: Any) -> dict[str, Any]:
        """Extract validation constraints from Pydantic field."""
        constraint_attributes = ['min_length', 'max_length', 'regex', 'ge', 'le', 'gt', 'lt']

        constraints = {}
        for attr in constraint_attributes:
            value = getattr(field, attr, None)
            if value is not None:
                constraints[attr] = value

        return constraints

    @classmethod
    def enrich_schema_with_constraints(cls, schema: dict[str, Any], model: Any) -> dict[str, Any]:
        """Add field constraints to OpenAPI schema."""
        if 'properties' not in schema:
            return schema

        for field_name, field in model.model_fields.items():
            if field_name in schema['properties']:
                constraints = cls.extract_field_constraints(field)
                schema['properties'][field_name].update(constraints)

        return schema

    @classmethod
    def generate_operation_content(cls, endpoint: Any, http_method: str, schemas: dict[str, Any]) -> dict[str, Any]:
        """Generate OpenAPI operation content for an endpoint."""
        # Skip if endpoint is excluded from docs
        if endpoint.output_schema and endpoint.output_schema.exclude_in_docs:
            return {}

        # Parse endpoint response
        response_parser = EndpointParser(endpoint, http_method)

        # Extract basic operation info
        operation_id = f'{response_parser.endpoint_name}_{http_method}'
        parameters = cls.extract_path_parameters(
            endpoint=endpoint, endpoint_name=response_parser.endpoint_name, http_method=http_method
        )
        summary, description = cls.parse_docstring(endpoint.__doc__)

        # Extract tags
        tags = cls._extract_operation_tags(endpoint=endpoint, response_parser=response_parser)

        # Extract metadata
        metadata = cls._extract_endpoint_metadata(endpoint=endpoint, description=description)

        # Handle response schema
        response_schema = cls._build_response_schema(
            endpoint=endpoint, response_parser=response_parser, schemas=schemas
        )

        # Handle request body
        request_body = cls._build_request_body(endpoint=endpoint, http_method=http_method, schemas=schemas)

        # Build operation content
        operation_content = {
            'operationId': operation_id,
            'summary': summary,
            'description': metadata['description'],
            'tags': tags,
            'parameters': parameters,
            'security': metadata['security'],
            'deprecated': metadata['deprecated'],
        }

        operation_content.update(response_schema)
        operation_content.update(request_body)

        return {http_method: operation_content}

    @classmethod
    def _extract_operation_tags(cls, endpoint: Any, response_parser: EndpointParser) -> list[str]:
        """Extract tags for operation grouping."""
        if endpoint.output_schema and endpoint.output_schema.tags:
            return endpoint.output_schema.tags
        return [response_parser.endpoint_name] if response_parser.endpoint_name else [endpoint.__module__]

    @classmethod
    def _extract_endpoint_metadata(cls, endpoint: Any, description: str) -> dict[str, Any]:
        """Extract metadata like permissions, throttling, etc."""
        # Extract permissions
        permissions = [p.__name__ for p in endpoint.permissions] if endpoint.permissions else None

        # Extract throttling
        throttling = None
        if endpoint.throttling:
            throttling = f'{endpoint.throttling.rate} per {endpoint.throttling.duration}'

        # Extract cache
        cache = str(endpoint.cache) if endpoint.cache else None

        # Extract middlewares
        middlewares = None
        if endpoint.middlewares:
            middlewares = [getattr(m, '__name__', str(m)) for m in endpoint.middlewares]

        # Extract deprecated status
        deprecated = endpoint.output_schema.deprecated if endpoint.output_schema else False

        # Build security
        security = [{'BearerAuth': []}] if endpoint.auth else []

        # Enhance description with metadata
        if permissions:
            description += f'<br>  - Permissions: {permissions}'
        if throttling:
            description += f'<br>  - Throttling: {throttling}'
        if cache:
            description += f'<br>  - Cache: {cache}'
        if middlewares:
            description += f'<br>  - Middlewares: {middlewares}'

        return {
            'description': description,
            'security': security,
            'deprecated': deprecated,
        }

    @classmethod
    def _build_response_schema(
        cls, endpoint: Any, response_parser: EndpointParser, schemas: dict[str, Any]
    ) -> dict[str, Any]:
        """Build response schema for the endpoint."""
        if endpoint.output_schema:
            status_code = endpoint.output_schema.status_code
            model = endpoint.output_schema.model
        elif endpoint.output_model:
            status_code = response_parser.status_code
            model = endpoint.output_model
        else:
            status_code = response_parser.status_code
            schema_ref = {'properties': {k: {'default': v} for k, v in response_parser.response_data.items()}}
            return {'responses': {status_code: {'content': {'application/json': {'schema': schema_ref}}}}}

        # Add model to schemas if not present
        model_name = cls.get_model_name(model)
        if model_name not in schemas:
            schema = model.schema(ref_template='#/components/schemas/{model}')
            schema = cls.enrich_schema_with_constraints(schema, model)
            schemas[model_name] = schema

        schema_ref = {'$ref': f'#/components/schemas/{model_name}'}

        # Build responses
        responses = {'responses': {status_code: {'content': {'application/json': {'schema': schema_ref}}}}}

        # Add error responses
        if error_responses := cls._build_error_responses(endpoint):
            responses['responses'] |= error_responses

        return responses

    @classmethod
    def _build_error_responses(cls, endpoint: Any) -> dict[int, dict[str, str]]:
        """Build standard error responses for the endpoint."""
        error_responses = {}

        if endpoint.auth:
            error_responses[401] = {'description': 'Unauthorized'}
        if endpoint.permissions:
            error_responses[403] = {'description': 'Forbidden'}
        if endpoint.input_model:
            error_responses[400] = {'description': 'Bad Request'}
            error_responses[422] = {'description': 'Unprocessable Entity'}

        return error_responses

    @classmethod
    def _build_request_body(cls, endpoint: Any, http_method: str, schemas: dict[str, Any]) -> dict[str, Any]:
        """Build request body schema for the endpoint."""
        if not (endpoint.input_model and http_method in cls.REQUEST_BODY_METHODS):
            return {}

        model = endpoint.input_model
        model_name = cls.get_model_name(model)

        # Add model to schemas if not present
        if model_name not in schemas:
            schema = model.schema(ref_template='#/components/schemas/{model}')
            schema = cls.enrich_schema_with_constraints(schema, model)
            schemas[model_name] = schema

        return {
            'requestBody': {
                'required': True,
                'content': {'application/json': {'schema': {'$ref': f'#/components/schemas/{model_name}'}}},
            }
        }

    @classmethod
    def generate_openapi_spec(cls) -> dict[str, Any]:
        """
        Generate complete OpenAPI 3.0 specification.

        Returns:
            Complete OpenAPI specification dictionary
        """
        paths = {}
        schemas = {}

        # Process all registered endpoints
        for url, endpoint in config.FLAT_URLS.items():
            url = url.replace('<', '{').replace('>', '}')
            if not url.startswith('/'):
                url = f'/{url}'
            paths[url] = {}

            if isinstance(endpoint, types.FunctionType):
                # Function-based endpoints
                for method in cls.HTTP_METHODS:
                    if method.upper() in endpoint.methods:
                        paths[url].update(cls.generate_operation_content(endpoint, method, schemas))
            else:
                # Class-based endpoints
                for method in cls.HTTP_METHODS:
                    # Check if method is overridden (not the default GenericAPI method)
                    if getattr(endpoint, method) is not getattr(GenericAPI, method):
                        paths[url].update(cls.generate_operation_content(endpoint, method, schemas))

        # Build security schemes
        security_schemes = {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }

        # Build complete OpenAPI specification
        openapi_spec = {
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

        return openapi_spec
