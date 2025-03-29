import contextlib
import logging
import sys
import types
from collections.abc import Callable
from logging.config import dictConfig
from pathlib import Path

import panther.logging
from panther import status
from panther._load_configs import *
from panther._utils import traceback_message, reformat_code
from panther.cli.utils import print_info
from panther.configs import config
from panther.events import Event
from panther.exceptions import APIError, PantherError, NotFoundAPIError
from panther.monitoring import Monitoring
from panther.request import Request
from panther.response import Response
from panther.routings import find_endpoint

dictConfig(panther.logging.LOGGING)
logger = logging.getLogger('panther')


class Panther:
    def __init__(self, name: str, configs: str | None = None, urls: dict | None = None):
        self._configs_module_name = configs
        self._urls = urls

        config.BASE_DIR = Path(name).resolve().parent

        try:
            self.load_configs()
            if config.AUTO_REFORMAT:
                reformat_code(base_dir=config.BASE_DIR)
        except Exception as e:  # noqa: BLE001
            logger.error(e.args[0] if isinstance(e, PantherError) else traceback_message(exception=e))
            sys.exit()

        # Print Info
        print_info(config)

    def load_configs(self) -> None:
        # Check & Read The Configs File
        self._configs_module = load_configs_module(self._configs_module_name)

        load_redis(self._configs_module)
        load_startup(self._configs_module)
        load_shutdown(self._configs_module)
        load_timezone(self._configs_module)
        load_database(self._configs_module)
        load_secret_key(self._configs_module)
        load_monitoring(self._configs_module)
        load_throttling(self._configs_module)
        load_user_model(self._configs_module)
        load_log_queries(self._configs_module)
        load_templates_dir(self._configs_module)
        load_middlewares(self._configs_module)
        load_auto_reformat(self._configs_module)
        load_background_tasks(self._configs_module)
        load_default_cache_exp(self._configs_module)
        load_authentication_class(self._configs_module)
        load_urls(self._configs_module, urls=self._urls)
        load_websocket_connections()

        check_endpoints_inheritance()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope['type'] == 'lifespan':
            message = await receive()
            if message["type"] == 'lifespan.startup':
                if config.HAS_WS:
                    await config.WEBSOCKET_CONNECTIONS.start()
                await Event.run_startups()
            elif message["type"] == 'lifespan.shutdown':
                # It's not happening :\, so handle the shutdowns in __del__ ...
                pass
            return

        func = self.handle_http if scope['type'] == 'http' else self.handle_ws
        await func(scope=scope, receive=receive, send=send)

    async def handle_ws(self, scope: dict, receive: Callable, send: Callable) -> None:
        from panther.websocket import GenericWebsocket, Websocket

        # Monitoring
        monitoring = Monitoring(is_ws=True)

        # Create Temp Connection
        temp_connection = Websocket(scope=scope, receive=receive, send=send)
        await monitoring.before(request=temp_connection)
        temp_connection._monitoring = monitoring

        # Find Endpoint
        endpoint, found_path = find_endpoint(path=temp_connection.path)
        if endpoint is None:
            logger.debug(f'Path `{temp_connection.path}` not found')
            return await temp_connection.close()

        # Check Endpoint Type
        if not issubclass(endpoint, GenericWebsocket):
            logger.critical(f'You may have forgotten to inherit from `GenericWebsocket` on the `{endpoint.__name__}()`')
            return await temp_connection.close()

        # Create The Connection
        del temp_connection
        connection = endpoint(scope=scope, receive=receive, send=send)
        connection._monitoring = monitoring

        # Collect Path Variables
        connection.collect_path_variables(found_path=found_path)

        middlewares = [middleware() for middleware in config.WS_MIDDLEWARES]

        # Call Middlewares .before()
        await self._run_ws_middlewares_before_listen(connection=connection, middlewares=middlewares)

        # Listen The Connection
        await config.WEBSOCKET_CONNECTIONS.listen(connection=connection)

        # Call Middlewares .after()
        middlewares.reverse()
        await self._run_ws_middlewares_after_listen(connection=connection, middlewares=middlewares)

    @classmethod
    async def _run_ws_middlewares_before_listen(cls, *, connection, middlewares):
        try:
            for middleware in middlewares:
                new_connection = await middleware.before(request=connection)
                if new_connection is None:
                    logger.critical(
                        f'Make sure to return the `request` at the end of `{middleware.__class__.__name__}.before()`')
                    await connection.close()
                connection = new_connection
        except APIError as e:
            connection.log(e.detail)
            await connection.close()

    @classmethod
    async def _run_ws_middlewares_after_listen(cls, *, connection, middlewares):
        for middleware in middlewares:
            with contextlib.suppress(APIError):
                connection = await middleware.after(response=connection)
                if connection is None:
                    logger.critical(
                        f'Make sure to return the `response` at the end of `{middleware.__class__.__name__}.after()`')
                    break

    @classmethod
    async def handle_http_endpoint(cls, request: Request) -> Response:
        # Find Endpoint
        endpoint, found_path = find_endpoint(path=request.path)
        if endpoint is None:
            raise NotFoundAPIError

        # Collect Path Variables
        request.collect_path_variables(found_path=found_path)

        # Prepare the method
        if not isinstance(endpoint, types.FunctionType):
            endpoint = endpoint().call_method
        # Call Endpoint
        return await endpoint(request=request)

    async def handle_http(self, scope: dict, receive: Callable, send: Callable) -> None:
        # Create `Request` and its body
        request = Request(scope=scope, receive=receive, send=send)
        await request.read_body()

        # Create Middlewares chain
        chained_func = self.handle_http_endpoint
        for middleware in reversed(config.HTTP_MIDDLEWARES):
            chained_func = middleware(dispatch=chained_func)

        # Call Middlewares & Endpoint
        try:
            response = await chained_func(request=request)

        # Handle `APIError` Exceptions
        except APIError as e:
            response = Response(
                data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
                status_code=e.status_code,
            )

        # Handle Unknown Exceptions
        except Exception as e:  # noqa: BLE001 - Blind Exception
            logger.error(traceback_message(exception=e))
            response = Response(
                data={'detail': 'Internal Server Error'},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return Response
        await response.send(send, receive)

    def __del__(self):
        Event.run_shutdowns()
