import functools
import logging
from datetime import timedelta
from typing import Literal

from orjson import JSONDecodeError
from pydantic import ValidationError, BaseModel

from panther._utils import is_function_async
from panther.caching import (
    get_response_from_cache,
    set_response_in_cache,
    get_throttling_from_cache,
    increment_throttling_in_cache
)
from panther.configs import config
from panther.exceptions import (
    APIError,
    AuthorizationAPIError,
    JSONDecodeAPIError,
    MethodNotAllowedAPIError,
    ThrottlingAPIError,
    BadRequestAPIError
)
from panther.middlewares import BaseMiddleware
from panther.openapi import OutputSchema
from panther.permissions import BasePermission
from panther.request import Request
from panther.response import Response
from panther.serializer import ModelSerializer
from panther.throttling import Throttling

__all__ = ('API', 'GenericAPI')

logger = logging.getLogger('panther')


class API:
    """
    input_model: The `request.data` will be validated with this attribute, It will raise an
        `panther.exceptions.BadRequestAPIError` or put the validated data in the `request.validated_data`.
    output_schema: This attribute only used in creation of OpenAPI scheme which is available in `panther.openapi.urls`
        You may want to add its `url` to your urls.
    auth: It will authenticate the user with header of its request or raise an
        `panther.exceptions.AuthenticationAPIError`.
    permissions: List of permissions that will be called sequentially after authentication to authorize the user.
    throttling: It will limit the users' request on a specific (time-bucket, path)
    cache: Response of the request will be cached.
    cache_exp_time: Specify the expiry time of the cache. (default is `config.DEFAULT_CACHE_EXP`)
    methods: Specify the allowed methods.
    middlewares: These middlewares have inner priority than global middlewares.
    """

    def __init__(
        self,
        *,
        input_model: type[ModelSerializer] | type[BaseModel] | None = None,
        output_schema: OutputSchema | None = None,
        auth: bool = False,
        permissions: list[BasePermission] | None = None,
        throttling: Throttling | None = None,
        cache: bool = False,
        cache_exp_time: timedelta | int | None = None,
        methods: list[Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']] | None = None,
        middlewares: list[BaseMiddleware] | None = None,
    ):
        self.input_model = input_model
        self.output_schema = output_schema
        self.auth = auth
        self.permissions = permissions or []
        self.throttling = throttling
        self.cache = cache
        self.cache_exp_time = cache_exp_time
        self.methods = {m.upper() for m in methods} if methods else None
        self.middlewares: list[BaseMiddleware] | None = middlewares
        self.request: Request | None = None

    def __call__(self, func):
        @functools.wraps(func)
        async def wrapper(request: Request) -> Response:
            self.request = request

            middlewares = [m() for m in self.middlewares or []]
            for middleware in middlewares:
                request = await middleware.before(request=request)

            # 0. Preflight
            if self.request.method == 'OPTIONS':
                return self.options()

            # 1. Check Method
            if self.methods and self.request.method not in self.methods:
                raise MethodNotAllowedAPIError

            # 2. Authentication
            await self.handle_authentication()

            # 3. Permissions
            await self.handle_permission()

            # 4. Throttling
            await self.handle_throttling()

            # 5. Validate Input
            if self.request.method in {'POST', 'PUT', 'PATCH'}:
                self.handle_input_validation()

            # 6. Get Cached Response
            if self.cache and self.request.method == 'GET':
                if cached := await get_response_from_cache(request=self.request, cache_exp_time=self.cache_exp_time):
                    return Response(data=cached.data, headers=cached.headers, status_code=cached.status_code)

            # 7. Put PathVariables and Request(If User Wants It) In kwargs
            kwargs = self.request.clean_parameters(func)

            # 8. Call Endpoint
            if is_function_async(func):
                response = await func(**kwargs)
            else:
                response = func(**kwargs)

            # 9. Clean Response
            if not isinstance(response, Response):
                response = Response(data=response)
            if self.output_schema and response.data:
                response.data = await response.apply_output_model(output_model=self.output_schema.model)
            if response.pagination:
                response.data = await response.pagination.template(response.data)

            # 10. Set New Response To Cache
            if self.cache and self.request.method == 'GET':
                await set_response_in_cache(request=self.request, response=response, cache_exp_time=self.cache_exp_time)

            # 11. Warning CacheExpTime
            if self.cache_exp_time and self.cache is False:
                logger.warning('"cache_exp_time" won\'t work while "cache" is False')

            middlewares.reverse()
            for middleware in middlewares:
                response = await middleware.after(response=response)

            return response

        # Store attributes on the function, so have the same behaviour as class-based (useful in `openapi.view.OpenAPI`)
        wrapper.auth = self.auth
        wrapper.methods = self.methods
        wrapper.permissions = self.permissions
        wrapper.input_model = self.input_model
        wrapper.output_schema = self.output_schema
        return wrapper

    async def handle_authentication(self) -> None:
        if self.auth:
            if not config.AUTHENTICATION:
                logger.critical('"AUTHENTICATION" has not been set in configs')
                raise APIError
            self.request.user = await config.AUTHENTICATION.authentication(self.request)

    async def handle_throttling(self) -> None:
        if throttling := self.throttling or config.THROTTLING:
            if await get_throttling_from_cache(self.request, duration=throttling.duration) + 1 > throttling.rate:
                raise ThrottlingAPIError

            await increment_throttling_in_cache(self.request, duration=throttling.duration)

    async def handle_permission(self) -> None:
        for perm in self.permissions:
            if type(perm.authorization).__name__ != 'method':
                logger.error(f'{perm.__name__}.authorization should be "classmethod"')
                raise AuthorizationAPIError
            if await perm.authorization(self.request) is False:
                raise AuthorizationAPIError

    def handle_input_validation(self):
        if self.input_model:
            self.request.validated_data = self.validate_input(model=self.input_model, request=self.request)

    @classmethod
    def options(cls):
        headers = {
            'Access-Control-Allow-Methods': 'DELETE, GET, PATCH, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Accept, Authorization, User-Agent, Content-Type',
        }
        return Response(headers=headers)

    @classmethod
    def validate_input(cls, model, request: Request):
        if isinstance(request.data, bytes):
            raise BadRequestAPIError(detail='Content-Type is not valid')
        if request.data is None:
            raise BadRequestAPIError(detail='Request body is required')
        try:
            # `request` will be ignored in regular `BaseModel`
            return model(**request.data, request=request)
        except ValidationError as validation_error:
            error = {'.'.join(str(loc) for loc in e['loc']): e['msg'] for e in validation_error.errors()}
            raise BadRequestAPIError(detail=error)
        except JSONDecodeError:
            raise JSONDecodeAPIError


class GenericAPI:
    """
    Check out the documentation of `panther.app.API()`.
    """
    input_model: type[ModelSerializer] | type[BaseModel] | None = None
    output_schema: OutputSchema | None = None
    auth: bool = False
    permissions: list | None = None
    throttling: Throttling | None = None
    cache: bool = False
    cache_exp_time: timedelta | int | None = None
    middlewares: list[BaseMiddleware] | None = None

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
            case 'OPTIONS':
                func = API.options
            case _:
                raise MethodNotAllowedAPIError

        return await API(
            input_model=self.input_model,
            output_schema=self.output_schema,
            auth=self.auth,
            permissions=self.permissions,
            throttling=self.throttling,
            cache=self.cache,
            cache_exp_time=self.cache_exp_time,
            middlewares=self.middlewares,
        )(func)(request=request)
