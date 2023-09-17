import asyncio
import sys
import types
from pathlib import Path
from rich.console import Console
from threading import Thread

from panther import status
from panther._load_configs import *
from panther._utils import clean_traceback_message, http_response
from panther.configs import config
from panther.exceptions import APIException
from panther.middlewares.monitoring import Middleware as MonitoringMiddleware
from panther.request import Request
from panther.response import Response
from panther.routings import collect_path_variables, find_endpoint

""" We can't import logger on the top cause it needs config['base_dir'] ans its fill in __init__ """


class Panther:

    def __init__(self, name, configs=None, urls: dict | None = None):
        from panther.logger import logger

        self._configs = configs
        self._urls = urls
        config['base_dir'] = Path(name).resolve().parent
        if sys.version_info.minor < 11:
            logger.warning('Use Python Version 3.11+ For Better Performance.')

        try:
            self.load_configs()
        except TypeError:
            exit()

        Thread(target=self.websocket_connections, daemon=True, args=(self.ws_redis_connection,)).start()

    def load_configs(self) -> None:
        from panther.logger import logger
        logger.debug(f'Base directory: {config["base_dir"]}')

        # Check & Read The Configs File
        self.configs = load_configs_file(self._configs)

        self.console = Console()

        # Put Variables In "config" (Careful about the ordering)
        config['secret_key'] = load_secret_key(self.configs)
        config['monitoring'] = load_monitoring(self.configs)
        config['log_queries'] = load_log_queries(self.configs)
        config['throttling'] = load_throttling(self.configs)
        config['default_cache_exp'] = load_default_cache_exp(self.configs)
        config['middlewares'] = load_middlewares(self.configs)
        config['reversed_middlewares'] = config['middlewares'][::-1]
        config['user_model'] = load_user_model(self.configs)
        config['authentication'] = load_authentication_class(self.configs)
        config['jwt_config'] = load_jwt_config(self.configs)
        config['models'] = collect_all_models()

        # Create websocket connections instance
        from panther.websocket import WebsocketConnections
        config['websocket_connections'] = self.websocket_connections = WebsocketConnections()
        # Websocket Redis Connection
        for middleware in config['middlewares']:
            if middleware.__class__.__name__ == 'RedisMiddleware':
                # TODO: What if user define a middleware with same name?
                self.ws_redis_connection = middleware.redis_connection_for_ws()
                break
        else:
            self.ws_redis_connection = None

        # Load URLs should be the last call in load_configs,
        #   because it will read all files and load them.
        config['urls'] = load_urls(self.configs, urls=self._urls)
        config['urls']['_panel'] = load_panel_urls()

        if config['monitoring']:
            logger.info('Run "panther monitor" in another session for Monitoring.')

    async def __call__(self, scope, receive, send) -> None:
        """
        We Used Python3.11+ For asyncio.TaskGroup()
        1.
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.run(scope, receive, send))
        2.
            await self.run(scope, receive, send)
        3.
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(self.run, scope, receive, send)
                await anyio.to_thread.run_sync(self.run, scope, receive, send)
        4.
            with ProcessPoolExecutor() as e:
                e.submit(self.run, scope, receive, send)
        """
        func = self.handle_http if scope['type'] == 'http' else self.handle_ws

        if sys.version_info.minor >= 11:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(func(scope, receive, send))
        else:
            await func(scope, receive, send)

    async def handle_ws(self, scope, receive, send):
        from panther.logger import logger
        from panther.websocket import Websocket, GenericWebsocket

        temp_connection = Websocket(scope=scope, receive=receive, send=send)

        endpoint, found_path = find_endpoint(path=temp_connection.path)
        if endpoint is None:
            return await temp_connection.close(status.WS_1000_NORMAL_CLOSURE)
        path_variables: dict = collect_path_variables(request_path=temp_connection.path, found_path=found_path)

        if not issubclass(endpoint, GenericWebsocket):
            logger.critical(f'You may have forgotten to inherit from GenericWebsocket on the {endpoint.__name__}()')
            return await temp_connection.close(status.WS_1014_BAD_GATEWAY)

        del temp_connection
        connection = endpoint(scope=scope, receive=receive, send=send)
        connection.set_path_variables(path_variables=path_variables)

        # Call 'Before' Middlewares
        for middleware in config['middlewares']:
            try:
                connection = await middleware.before(request=connection)
            except APIException:
                await connection.close()
                break
        else:
            await self.websocket_connections.new_connection(connection=connection)
            await connection.listen()

        # Call 'After' Middleware
        for middleware in config['reversed_middlewares']:
            try:
                await middleware.after(response=connection)
            except APIException:
                pass

    async def handle_http(self, scope, receive, send):
        from panther.logger import logger

        request = Request(scope=scope, receive=receive, send=send)

        # Monitoring Middleware
        monitoring_middleware = None
        if config['monitoring']:
            monitoring_middleware = MonitoringMiddleware()
            await monitoring_middleware.before(request=request)

        # Read Request Payload
        await request.read_body()

        # Find Endpoint
        endpoint, found_path = find_endpoint(path=request.path)
        path_variables: dict = collect_path_variables(request_path=request.path, found_path=found_path)

        if endpoint is None:
            return await http_response(
                send, status_code=status.HTTP_404_NOT_FOUND, monitoring=monitoring_middleware, exception=True,
            )

        try:  # They Both(middleware.before() & _endpoint()) Have The Same Exception (APIException)
            # Call 'Before' Middlewares
            for middleware in config['middlewares']:
                request = await middleware.before(request=request)

            # Function
            if isinstance(endpoint, types.FunctionType):
                # Function Doesn't Have @API Decorator
                if not hasattr(endpoint, '__wrapped__'):
                    logger.critical(f'You may have forgotten to use @API on the {endpoint.__name__}()')
                    return await http_response(
                        send,
                        status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        monitoring=monitoring_middleware,
                        exception=True,
                    )

                # Declare Endpoint
                _endpoint = endpoint

            # Class
            else:
                from panther.app import GenericAPI

                if not issubclass(endpoint, GenericAPI):
                    logger.critical(f'You may have forgotten to inherit from GenericAPI on the {endpoint.__name__}()')
                    return await http_response(
                        send,
                        status_code=status.HTTP_501_NOT_IMPLEMENTED,
                        monitoring=monitoring_middleware,
                        exception=True,
                    )
                # Declare Endpoint
                _endpoint = endpoint.call_method

            # Call Endpoint
            response = await _endpoint(request=request, **path_variables)

        except APIException as e:
            response = self.handle_exceptions(e)
        except Exception as e:  # noqa: BLE001
            # Every unhandled exception in Panther or code will catch here
            exception = clean_traceback_message(exception=e)
            logger.critical(exception)

            return await http_response(
                send,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                monitoring=monitoring_middleware,
                exception=True,
            )

        # Call 'After' Middleware
        for middleware in config['reversed_middlewares']:
            try:
                response = await middleware.after(response=response)
            except APIException as e:  # noqa: PERF203
                response = self.handle_exceptions(e)

        await http_response(
            send,
            status_code=response.status_code,
            monitoring=monitoring_middleware,
            headers=response.headers,
            body=response.body,
        )

    @classmethod
    def handle_exceptions(cls, e, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code,
        )
