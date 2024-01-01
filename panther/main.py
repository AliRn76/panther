import asyncio
import contextlib
import logging
import sys
import types
from collections.abc import Callable
from logging.config import dictConfig
from pathlib import Path
from threading import Thread

import panther.logging
from panther import status
from panther._load_configs import *
from panther._utils import clean_traceback_message, http_response, is_function_async, reformat_code, \
    check_class_type_endpoint, check_function_type_endpoint
from panther.background_tasks import background_tasks
from panther.cli.utils import print_info
from panther.configs import config
from panther.exceptions import APIException, PantherException
from panther.monitoring import Monitoring
from panther.request import Request
from panther.response import Response
from panther.routings import collect_path_variables, find_endpoint

dictConfig(panther.logging.LOGGING)
logger = logging.getLogger('panther')


class Panther:
    def __init__(self, name: str, configs=None, urls: dict | None = None, startup: Callable = None, shutdown: Callable = None):
        self._configs_module_name = configs
        self._urls = urls
        self._startup = startup
        self._shutdown = shutdown

        config['base_dir'] = Path(name).resolve().parent

        try:
            self.load_configs()
            if config['auto_reformat']:
                reformat_code(base_dir=config['base_dir'])
        except Exception as e:  # noqa: BLE001
            if isinstance(e, PantherException):
                logger.error(e.args[0])
            else:
                logger.error(clean_traceback_message(e))
            sys.exit()

        # Monitoring
        self.monitoring = Monitoring(is_active=config['monitoring'])

        # Print Info
        print_info(config)

        # Start Websocket Listener (Redis Required)
        if config['has_ws']:
            Thread(
                target=config['websocket_connections'],
                daemon=True,
                args=(self.ws_redis_connection,),
            ).start()

    def load_configs(self) -> None:

        # Check & Read The Configs File
        self._configs_module = load_configs_module(self._configs_module_name)

        # Put Variables In "config" (Careful about the ordering)
        config['secret_key'] = load_secret_key(self._configs_module)
        config['monitoring'] = load_monitoring(self._configs_module)
        config['log_queries'] = load_log_queries(self._configs_module)
        config['background_tasks'] = load_background_tasks(self._configs_module)
        config['throttling'] = load_throttling(self._configs_module)
        config['default_cache_exp'] = load_default_cache_exp(self._configs_module)
        middlewares = load_middlewares(self._configs_module)
        config['http_middlewares'] = middlewares['http']
        config['ws_middlewares'] = middlewares['ws']
        config['reversed_http_middlewares'] = middlewares['http'][::-1]
        config['reversed_ws_middlewares'] = middlewares['ws'][::-1]
        config['user_model'] = load_user_model(self._configs_module)
        config['authentication'] = load_authentication_class(self._configs_module)
        config['jwt_config'] = load_jwt_config(self._configs_module)
        config['startup'] = load_startup(self._configs_module)
        config['shutdown'] = load_shutdown(self._configs_module)
        config['auto_reformat'] = load_auto_reformat(self._configs_module)
        config['models'] = collect_all_models()

        # Initialize Background Tasks
        if config['background_tasks']:
            background_tasks.initialize()

        # Load URLs should be one of the last calls in load_configs,
        #   because it will read all files and loads them.
        config['flat_urls'], config['urls'] = load_urls(self._configs_module, urls=self._urls)
        config['urls']['_panel'] = load_panel_urls()

        self._create_ws_connections_instance()

    def _create_ws_connections_instance(self):
        from panther.base_websocket import Websocket
        from panther.websocket import WebsocketConnections

        # Check do we have ws endpoint
        for endpoint in config['flat_urls'].values():
            if not isinstance(endpoint, types.FunctionType) and issubclass(endpoint, Websocket):
                config['has_ws'] = True
                break
        else:
            config['has_ws'] = False

        # Create websocket connections instance
        if config['has_ws']:
            config['websocket_connections'] = WebsocketConnections()
            # Websocket Redis Connection
            for middleware in config['middlewares']:
                if middleware.__class__.__name__ == 'RedisMiddleware':
                    self.ws_redis_connection = middleware.redis_connection_for_ws()
                    break
            else:
                self.ws_redis_connection = None

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """
        1.
            await func(scope, receive, send)
        2.
            async with asyncio.TaskGroup() as tg:
                tg.create_task(func(scope, receive, send))
        3.
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(func, scope, receive, send)
                await anyio.to_thread.run_sync(func, scope, receive, send)
        4.
            with ProcessPoolExecutor() as e:
                e.submit(func, scope, receive, send)
        """
        if scope['type'] == 'lifespan':
            message = await receive()
            if message["type"] == "lifespan.startup":
                await self.handle_startup()
            return

        func = self.handle_http if scope['type'] == 'http' else self.handle_ws
        await func(scope=scope, receive=receive, send=send)

    async def handle_ws(self, scope: dict, receive: Callable, send: Callable) -> None:
        from panther.websocket import GenericWebsocket, Websocket

        # Monitoring
        monitoring = Monitoring(is_active=config['monitoring'], is_ws=True)

        # Create Temp Connection
        temp_connection = Websocket(scope=scope, receive=receive, send=send)
        await monitoring.before(request=temp_connection)

        # Find Endpoint
        endpoint, found_path = find_endpoint(path=temp_connection.path)
        if endpoint is None:
            await monitoring.after('Rejected')
            return await temp_connection.close(status.WS_1000_NORMAL_CLOSURE)

        # Check Endpoint Type
        if not issubclass(endpoint, GenericWebsocket):
            logger.critical(f'You may have forgotten to inherit from GenericWebsocket on the {endpoint.__name__}()')
            await monitoring.after('Rejected')
            return await temp_connection.close(status.WS_1014_BAD_GATEWAY)

        # Collect Path Variables
        path_variables: dict = collect_path_variables(request_path=temp_connection.path, found_path=found_path)

        # Create The Connection
        del temp_connection
        connection = endpoint(scope=scope, receive=receive, send=send)
        connection.set_path_variables(path_variables=path_variables)

        # Call 'Before' Middlewares
        if await self._run_ws_middlewares_before_listen(connection=connection):
            # Only Listen() If Middlewares Didn't Raise Anything
            await config['websocket_connections'].new_connection(connection=connection)
            await monitoring.after('Accepted')
            await connection.listen()

        # Call 'After' Middlewares
        await self._run_ws_middlewares_after_listen(connection=connection)

        # Done
        await monitoring.after('Closed')
        return None

    @classmethod
    async def _run_ws_middlewares_before_listen(cls, *, connection) -> bool:
        for middleware in config['ws_middlewares']:
            try:
                connection = await middleware.before(request=connection)
            except APIException:
                await connection.close()
                return False
        return True

    @classmethod
    async def _run_ws_middlewares_after_listen(cls, *, connection):
        for middleware in config['reversed_ws_middlewares']:
            with contextlib.suppress(APIException):
                await middleware.after(response=connection)

    async def handle_http(self, scope: dict, receive: Callable, send: Callable) -> None:
        request = Request(scope=scope, receive=receive, send=send)

        # Monitoring
        await self.monitoring.before(request=request)

        # Read Request Payload
        await request.read_body()

        # Find Endpoint
        _endpoint, found_path = find_endpoint(path=request.path)
        if _endpoint is None:
            return await self._raise(send, status_code=status.HTTP_404_NOT_FOUND)

        # Check Endpoint Type
        try:
            if isinstance(_endpoint, types.FunctionType):
                endpoint = check_function_type_endpoint(endpoint=_endpoint)
            else:
                endpoint = check_class_type_endpoint(endpoint=_endpoint)
        except TypeError:
            return await self._raise(send, status_code=status.HTTP_501_NOT_IMPLEMENTED)

        # Collect Path Variables
        path_variables: dict = collect_path_variables(request_path=request.path, found_path=found_path)

        try:  # They Both(middleware.before() & _endpoint()) Have The Same Exception (APIException)
            # Call 'Before' Middlewares
            for middleware in config['http_middlewares']:
                request = await middleware.before(request=request)

            # Call Endpoint
            response = await endpoint(request=request, **path_variables)

        except APIException as e:
            response = self._handle_exceptions(e)

        except Exception as e:  # noqa: BLE001
            # Every unhandled exception in Panther or code will catch here
            exception = clean_traceback_message(exception=e)
            logger.critical(exception)
            return await self._raise(send, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Call 'After' Middleware
        for middleware in config['reversed_http_middlewares']:
            try:
                response = await middleware.after(response=response)
            except APIException as e:  # noqa: PERF203
                response = self._handle_exceptions(e)

        await http_response(
            send,
            status_code=response.status_code,
            monitoring=self.monitoring,
            headers=response.headers,
            body=response.body,
        )

    async def handle_startup(self):
        if startup := config['startup'] or self._startup:
            if is_function_async(startup):
                await startup()
            else:
                startup()

    def handle_shutdown(self):
        if shutdown := config['shutdown'] or self._shutdown:
            if is_function_async(shutdown):
                asyncio.run(shutdown())
            else:
                shutdown()

    def __del__(self):
        self.handle_shutdown()

    @classmethod
    def _handle_exceptions(cls, e: APIException, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code,
        )

    async def _raise(self, send, *, status_code: int):
        await http_response(
            send,
            status_code=status_code,
            monitoring=self.monitoring,
            exception=True,
        )
