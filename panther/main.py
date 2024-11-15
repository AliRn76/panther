import contextlib
import logging
import sys
import types
from collections.abc import Callable
from logging.config import dictConfig
from pathlib import Path

import orjson as json

import panther.logging
from panther import status
from panther._load_configs import *
from panther._utils import traceback_message, reformat_code
from panther.cli.utils import print_info
from panther.configs import config
from panther.events import Event
from panther.exceptions import APIError, PantherError
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

        middlewares = [middleware(**data) for middleware, data in config.WS_MIDDLEWARES]

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

    async def handle_http(self, scope: dict, receive: Callable, send: Callable) -> None:
        # Monitoring
        monitoring = Monitoring()

        request = Request(scope=scope, receive=receive, send=send)

        await monitoring.before(request=request)

        # Read Request Payload
        await request.read_body()

        # Find Endpoint
        endpoint, found_path = find_endpoint(path=request.path)
        if endpoint is None:
            return await self._raise(send, monitoring=monitoring, status_code=status.HTTP_404_NOT_FOUND)

        # Collect Path Variables
        request.collect_path_variables(found_path=found_path)

        middlewares = [middleware(**data) for middleware, data in config.HTTP_MIDDLEWARES]
        try:  # They Both(middleware.before() & _endpoint()) Have The Same Exception (APIError)
            # Call Middlewares .before()
            for middleware in middlewares:
                request = await middleware.before(request=request)
                if request is None:
                    logger.critical(
                        f'Make sure to return the `request` at the end of `{middleware.__class__.__name__}.before()`')
                    return await self._raise(send, monitoring=monitoring)

            # Prepare the method
            if not isinstance(endpoint, types.FunctionType):
                endpoint = endpoint().call_method

            # Call Endpoint
            response = await endpoint(request=request)

        except APIError as e:
            response = self._handle_exceptions(e)

        except Exception as e:  # noqa: BLE001
            # All unhandled exceptions are caught here
            exception = traceback_message(exception=e)
            logger.error(exception)
            return await self._raise(send, monitoring=monitoring)

        # Call Middlewares .after()
        middlewares.reverse()
        for middleware in middlewares:
            try:
                response = await middleware.after(response=response)
                if response is None:
                    logger.critical(
                        f'Make sure to return the `response` at the end of `{middleware.__class__.__name__}.after()`')
                    return await self._raise(send, monitoring=monitoring)
            except APIError as e:  # noqa: PERF203
                response = self._handle_exceptions(e)

        await response.send(send, receive, monitoring=monitoring)

    def __del__(self):
        Event.run_shutdowns()

    @classmethod
    def _handle_exceptions(cls, e: APIError, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code,
        )

    @classmethod
    async def _raise(cls, send, *, monitoring, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        headers = [[b'Content-Type', b'application/json']]
        body = json.dumps({'detail': status.status_text[status_code]})
        await monitoring.after(status_code)
        await send({'type': 'http.response.start', 'status': status_code, 'headers': headers})
        await send({'type': 'http.response.body', 'body': body, 'more_body': False})
