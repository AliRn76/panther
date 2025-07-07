import logging
import sys
from collections.abc import Callable
from logging.config import dictConfig
from pathlib import Path

import panther.logging
from panther import status
from panther._load_configs import *
from panther._utils import ENDPOINT_CLASS_BASED_API, ENDPOINT_FUNCTION_BASED_API, reformat_code, traceback_message
from panther.base_websocket import Websocket
from panther.cli.utils import print_info
from panther.configs import config
from panther.events import Event
from panther.exceptions import APIError, BaseError, NotFoundAPIError, PantherError, UpgradeRequiredError
from panther.request import Request
from panther.response import Response
from panther.routings import find_endpoint
from panther.websocket import GenericWebsocket

dictConfig(panther.logging.LOGGING)
logger = logging.getLogger('panther')


class Panther:
    def __init__(self, name: str, configs: str | None = None, urls: dict | None = None):
        """
        Initialize a Panther application instance.

        Args:
            name: Typically set to `__name__`; used to determine the current directory of the application.
            configs: The name of the module containing your configuration.
                If the configuration is defined in the current file, you can also set this to `__name__`.
            urls: A dictionary containing your URL routing.
                If not provided, Panther will attempt to load `URLs` from the configs module.

        """
        self._configs_module_name = configs
        self._urls = urls

        config.BASE_DIR = Path(name).resolve().parent

        try:
            self.load_configs()
            if config.AUTO_REFORMAT:
                reformat_code(base_dir=config.BASE_DIR)
        except Exception as e:
            logger.error(e.args[0] if isinstance(e, PantherError) else traceback_message(exception=e))
            sys.exit()

        # Print Info
        print_info(config)

    def load_configs(self) -> None:
        # Check & Read The Configs File
        self._configs_module = load_configs_module(self._configs_module_name)

        load_redis(self._configs_module)
        load_timezone(self._configs_module)
        load_database(self._configs_module)
        load_secret_key(self._configs_module)
        load_throttling(self._configs_module)
        load_user_model(self._configs_module)
        load_log_queries(self._configs_module)
        load_templates_dir(self._configs_module)
        load_middlewares(self._configs_module)
        load_auto_reformat(self._configs_module)
        load_background_tasks(self._configs_module)
        load_other_configs(self._configs_module)
        load_urls(self._configs_module, urls=self._urls)
        load_authentication_class(self._configs_module)
        load_websocket_connections()

        check_endpoints_inheritance()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope['type'] == 'http':
            await self.handle_http(scope=scope, receive=receive, send=send)
        elif scope['type'] == 'websocket':
            await self.handle_ws(scope=scope, receive=receive, send=send)
        elif scope['type'] == 'lifespan':
            message = await receive()
            if message['type'] == 'lifespan.startup':
                if config.HAS_WS:
                    await config.WEBSOCKET_CONNECTIONS.start()
                await Event.run_startups()
            elif message['type'] == 'lifespan.shutdown':
                pass
            return

    @staticmethod
    async def handle_ws_endpoint(connection: Websocket):
        # Find Endpoint
        endpoint, found_path = find_endpoint(path=connection.path)
        if endpoint is None:
            logger.debug(f'Path `{connection.path}` not found')
            await connection.close()
            return connection

        # Check Endpoint Type
        if not issubclass(endpoint, GenericWebsocket):
            logger.warning(f'{endpoint.__name__}() class is not a Websocket class.')
            await connection.close()
            return connection

        # Create The Connection
        final_connection = endpoint(parent=connection)
        del connection

        # Collect Path Variables
        final_connection.collect_path_variables(found_path=found_path)

        return await config.WEBSOCKET_CONNECTIONS.listen(connection=final_connection)

    @classmethod
    async def handle_ws(cls, scope: dict, receive: Callable, send: Callable) -> None:
        # Create Temp Connection
        connection = Websocket(scope=scope, receive=receive, send=send)

        # Create Middlewares chain
        chained_func = cls.handle_ws_endpoint
        for middleware in reversed(config.WS_MIDDLEWARES):
            chained_func = middleware(dispatch=chained_func)

        # Call Middlewares & Endpoint
        try:
            connection = await chained_func(connection=connection)
        except BaseError as e:
            connection.log(e.detail)
            await connection.close()
        except Exception as e:
            logger.error(traceback_message(exception=e))
            await connection.close()

    @staticmethod
    async def handle_http_endpoint(request: Request) -> Response:
        # Find Endpoint
        endpoint, found_path = find_endpoint(path=request.path)
        if endpoint is None:
            raise NotFoundAPIError

        # Collect Path Variables
        request.collect_path_variables(found_path=found_path)

        if endpoint._endpoint_type is ENDPOINT_FUNCTION_BASED_API:
            return await endpoint(request=request)
        if endpoint._endpoint_type is ENDPOINT_CLASS_BASED_API:
            return await endpoint().call_method(request=request)

        # ENDPOINT_WEBSOCKET
        raise UpgradeRequiredError

    @classmethod
    async def handle_http(cls, scope: dict, receive: Callable, send: Callable) -> None:
        # Create `Request` and its body
        request = Request(scope=scope, receive=receive, send=send)
        await request.read_body()

        # Create Middlewares chain
        chained_func = cls.handle_http_endpoint
        for middleware in reversed(config.HTTP_MIDDLEWARES):
            chained_func = middleware(dispatch=chained_func)

        # Call Middlewares & Endpoint
        try:
            response = await chained_func(request=request)
            if response is None:
                logger.error('You forgot to return `response` on the `Middlewares.__call__()`')
                response = Response(
                    data={'detail': 'Internal Server Error'},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        # Handle `APIError` Exceptions
        except APIError as e:
            response = Response(
                data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
                headers=e.headers,
                status_code=e.status_code,
            )
        # Handle Unknown Exceptions
        except Exception as e:
            logger.error(traceback_message(exception=e))
            response = Response(
                data={'detail': 'Internal Server Error'},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return Response
        await response.send(send=send, receive=receive)

    def __del__(self):
        Event.run_shutdowns()
