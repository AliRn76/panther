import asyncio
import sys
import types
from pathlib import Path

from panther import status
from panther._load_configs import *
from panther._utils import clean_traceback_message, http_response, read_body
from panther.configs import config
from panther.exceptions import APIException
from panther.middlewares.monitoring import Middleware as MonitoringMiddleware
from panther.request import Request
from panther.response import Response
from panther.routings import collect_path_variables, find_endpoint

""" We can't import logger on the top cause it needs config['base_dir'] ans its fill in __init__ """


class Panther:

    def __init__(self, name, configs=None):
        from panther.logger import logger

        self._configs = configs
        config['base_dir'] = Path(name).resolve().parent
        if sys.version_info.minor < 11:
            logger.warning('Use Python Version 3.11+ For Better Performance.')

        try:
            self.load_configs()
        except TypeError:
            exit()

    def load_configs(self) -> None:
        from panther.logger import logger
        logger.debug(f'Base directory: {config["base_dir"]}')

        # Check & Read The Configs File
        self.configs = load_configs_file(self._configs)

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

        # Load URLs should be the last call in load_configs,
        #   because it will read all files and load them.
        config['urls'] = load_urls(self.configs)
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
        if sys.version_info.minor >= 11:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.run(scope, receive, send))
        else:
            await self.run(scope, receive, send)

    async def run(self, scope, receive, send):
        from panther.logger import logger

        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)

        # Monitoring Middleware
        monitoring_middleware = None
        if config['monitoring']:
            monitoring_middleware = MonitoringMiddleware()
            await monitoring_middleware.before(request=request)

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
