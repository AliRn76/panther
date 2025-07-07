import functools
import inspect
import logging
import typing
from collections.abc import Callable
from datetime import timedelta
from typing import Literal

from pydantic import BaseModel

from panther._utils import (
    ENDPOINT_CLASS_BASED_API,
    ENDPOINT_FUNCTION_BASED_API,
    check_api_deprecations,
    is_function_async,
    validate_api_auth,
    validate_api_permissions,
)
from panther.base_request import BaseRequest
from panther.caching import (
    get_response_from_cache,
    set_response_in_cache,
)
from panther.configs import config
from panther.exceptions import (
    AuthorizationAPIError,
    MethodNotAllowedAPIError,
)
from panther.middlewares import HTTPMiddleware
from panther.openapi import OutputSchema
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer
from panther.throttling import Throttle

__all__ = ('API', 'GenericAPI')

logger = logging.getLogger('panther')


class API:
    """
    methods: Specify the allowed methods.
    input_model: The `request.data` will be validated with this attribute, It will raise an
        `panther.exceptions.BadRequestAPIError` or put the validated data in the `request.validated_data`.
    output_model: The `response.data` will be passed through this class to filter its attributes.
    output_schema: This attribute only used in creation of OpenAPI scheme which is available in `panther.openapi.urls`
        You may want to add its `url` to your urls.
    auth: It will authenticate the user with header of its request or raise an
        `panther.exceptions.AuthenticationAPIError`.
    permissions: List of permissions that will be called sequentially after authentication to authorize the user.
    throttling: It will limit the users' request on a specific (time-window, path)
    cache: Specify the duration of the cache (Will be used only in GET requests).
    middlewares: These middlewares have inner priority than global middlewares.
    """

    func: Callable

    def __init__(
        self,
        *,
        methods: list[Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']] | None = None,
        input_model: type[ModelSerializer] | type[BaseModel] | None = None,
        output_model: type[ModelSerializer] | type[BaseModel] | None = None,
        output_schema: OutputSchema | None = None,
        auth: Callable | None = None,
        permissions: list[Callable] | Callable | None = None,
        throttling: Throttle | None = None,
        cache: timedelta | None = None,
        middlewares: list[type[HTTPMiddleware]] | None = None,
        **kwargs,
    ):
        self.methods = {m.upper() for m in methods} if methods else {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}
        self.input_model = input_model
        self.output_model = output_model
        self.output_schema = output_schema
        self.auth = auth
        self.permissions = permissions
        if self.permissions is not None and not isinstance(self.permissions, list):
            self.permissions = [self.permissions]
        self.throttling = throttling
        self.cache = cache
        self.middlewares = middlewares
        self.request: Request | None = None
        if self.auth is not None:
            validate_api_auth(self.auth)
        validate_api_permissions(self.permissions)
        check_api_deprecations(self.cache, **kwargs)

    def __call__(self, func):
        self.func = func
        self.is_function_async = is_function_async(self.func)
        self.function_annotations = {
            k: v for k, v in func.__annotations__.items() if v in {BaseRequest, Request, bool, int}
        }

        @functools.wraps(func)
        async def wrapper(request: Request) -> Response:
            chained_func = self.handle_endpoint
            if self.middlewares:
                for middleware in reversed(self.middlewares):
                    chained_func = middleware(chained_func)
            return await chained_func(request=request)

        # Store attributes on the function, so have the same behaviour as class-based (useful in `openapi.view.OpenAPI`)
        wrapper.auth = self.auth
        wrapper.cache = self.cache
        wrapper.methods = self.methods
        wrapper.throttling = self.throttling
        wrapper.permissions = self.permissions
        wrapper.middlewares = self.middlewares
        wrapper.input_model = self.input_model
        wrapper.output_model = self.output_model
        wrapper.output_schema = self.output_schema
        wrapper._endpoint_type = ENDPOINT_FUNCTION_BASED_API
        return wrapper

    async def handle_endpoint(self, request: Request) -> Response:
        self.request = request

        # 1. Check Method
        if self.request.method not in self.methods:
            raise MethodNotAllowedAPIError

        # 2. Authentication
        if auth := (self.auth or config.AUTHENTICATION):
            if inspect.isclass(auth):
                auth = auth()
            self.request.user = await auth(self.request)

        # 3. Permissions
        if self.permissions:
            for perm in self.permissions:
                if inspect.isclass(perm):
                    perm = perm()
                if await perm(self.request) is False:
                    raise AuthorizationAPIError

        # 4. Throttle
        if throttling := (self.throttling or config.THROTTLING):
            await throttling.check_and_increment(request=self.request)

        # 5. Validate Input
        if self.input_model and self.request.method in {'POST', 'PUT', 'PATCH'}:
            self.request.validate_data(model=self.input_model)

        # 6. Get Cached Response
        if self.cache and self.request.method == 'GET':
            if cached := await get_response_from_cache(request=self.request, duration=self.cache):
                return Response(data=cached.data, headers=cached.headers, status_code=cached.status_code)

        # 7. Put PathVariables and Request(If User Wants It) In kwargs
        kwargs = self.request.clean_parameters(self.function_annotations)

        # 8. Call Endpoint
        if self.is_function_async:
            response = await self.func(**kwargs)
        else:
            response = self.func(**kwargs)

        # 9. Clean Response
        if not isinstance(response, Response):
            response = Response(data=response)
        if self.output_model and response.data:
            await response.serialize_output(output_model=self.output_model)
        if response.pagination:
            response.data = await response.pagination.template(response.data)

        # 10. Set New Response To Cache
        if self.cache and self.request.method == 'GET':
            await set_response_in_cache(request=self.request, response=response, duration=self.cache)

        return response


class MetaGenericAPI(type):
    def __new__(cls, cls_name: str, bases: tuple[type[typing.Any], ...], namespace: dict[str, typing.Any], **kwargs):
        if cls_name == 'GenericAPI':
            return super().__new__(cls, cls_name, bases, namespace)
        # Deprecated messages can be here
        # e.g. if 'something' in namespace:
        #          raise PantherError(deprecated_message)
        return super().__new__(cls, cls_name, bases, namespace)


class GenericAPI(metaclass=MetaGenericAPI):
    """
    Check out the documentation of `panther.app.API()`.
    """

    _endpoint_type = ENDPOINT_CLASS_BASED_API

    input_model: type[ModelSerializer] | type[BaseModel] | None = None
    output_model: type[ModelSerializer] | type[BaseModel] | None = None
    output_schema: OutputSchema | None = None
    auth: Callable | None = None
    permissions: list[Callable] | Callable | None = None
    throttling: Throttle | None = None
    cache: timedelta | None = None
    middlewares: list[HTTPMiddleware] | None = None

    def __init_subclass__(cls, **kwargs):
        if cls.permissions is not None and not isinstance(cls.permissions, list):
            cls.permissions = [cls.permissions]
        # Creating API instance to validate the attributes.
        API(
            input_model=cls.input_model,
            output_model=cls.output_model,
            output_schema=cls.output_schema,
            auth=cls.auth,
            permissions=cls.permissions,
            throttling=cls.throttling,
            cache=cls.cache,
            middlewares=cls.middlewares,
        )

    async def get(self, *args, **kwargs):
        raise MethodNotAllowedAPIError

    async def post(self, *args, **kwargs):
        raise MethodNotAllowedAPIError

    async def put(self, *args, **kwargs):
        raise MethodNotAllowedAPIError

    async def patch(self, *args, **kwargs):
        raise MethodNotAllowedAPIError

    async def delete(self, *args, **kwargs):
        raise MethodNotAllowedAPIError

    async def call_method(self, request: Request):
        match request.method:
            case 'GET':
                func = self.get
            case 'POST':
                func = self.post
            case 'PUT':
                func = self.put
            case 'PATCH':
                func = self.patch
            case 'DELETE':
                func = self.delete
            case _:
                raise MethodNotAllowedAPIError

        return await API(
            input_model=self.input_model,
            output_model=self.output_model,
            output_schema=self.output_schema,
            auth=self.auth,
            permissions=self.permissions,
            throttling=self.throttling,
            cache=self.cache,
            middlewares=self.middlewares,
        )(func)(request=request)
