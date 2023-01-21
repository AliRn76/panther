import anyio
from pathlib import Path
from runpy import run_path
from pydantic.main import ModelMetaclass

from panther import status
from panther.request import Request
from panther.response import Response
from panther.exceptions import APIException
from panther.configs import config, JWTConfig
from panther.middlewares.base import BaseMiddleware
from panther.middlewares.monitoring import Middleware as MonitoringMiddleware
from panther.utils import read_body, import_class, http_response

""" We can't import logger on the top cause it needs config['base_dir'] ans its fill in __init__ """


class Panther:

    def __init__(self, name):
        import os
        os.system('clear')
        self.base_dir = Path(name).resolve().parent
        config['base_dir'] = self.base_dir
        self.panther_dir = Path(__file__).parent
        self.load_configs()
        del os

    async def __call__(self, scope, receive, send) -> None:
        # await self.run(scope, receive, send)
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(self.run, scope, receive, send)
            # await anyio.to_thread.run_sync(self.run, scope, receive, send)
        # if self.exc_info is not None:
        #     raise self.exc_info[0].with_traceback(self.exc_info[1], self.exc_info[2])

        # with ProcessPoolExecutor() as e:
        #     e.submit(self.run, scope, receive, send)

    async def run(self, scope, receive, send):
        from panther.logger import logger, monitoring
        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)

        # Monitoring Middleware
        # TODO: Make it dynamic, only call if user wants monitoring
        monitoring_middleware = MonitoringMiddleware()
        await monitoring_middleware.before(request=request)

        # Find Endpoint
        endpoint = self.find_endpoint(path=request.path)
        if endpoint is None:
            return await http_response(
                send, status_code=status.HTTP_404_NOT_FOUND, monitoring=monitoring_middleware, exception=True
            )

        # Check Endpoint Method
        if endpoint.__module__ != 'panther.app':
            raise TypeError(f'You have to use API decorator on {endpoint.__module__}.{endpoint.__name__}()')
        endpoint_method = endpoint.__qualname__.split('.')[1].upper()
        if endpoint_method != scope['method']:
            return await http_response(
                send, status_code=status.HTTP_405_METHOD_NOT_ALLOWED, monitoring=monitoring_middleware, exception=True
            )

        try:
            # Call 'Before' Middlewares
            for middleware in config['middlewares']:
                request = await middleware.before(request=request)

            # Call Endpoint
            # TODO: Maybe we should move the caching here ...
            response = await endpoint(request=request)
        except APIException as e:
            response = self.handle_exceptions(e)
        except Exception as e:
            logger.critical(e)
            return await http_response(
                send,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                monitoring=monitoring_middleware,
                exception=True
            )

        # Call 'After' Middleware
        config['middlewares'].reverse()
        for middleware in config['middlewares']:
            try:
                response = await middleware.after(response=response)
            except APIException as e:
                response = self.handle_exceptions(e)

        await http_response(
            send, status_code=response.status_code, monitoring=monitoring_middleware, body=response.data
        )

    @classmethod
    def handle_exceptions(cls, e, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code
        )

    def load_user_model(self) -> ModelMetaclass:
        return import_class(self.settings.get('USER_MODEL', 'panther.db.models.User'))

    def load_configs(self) -> None:
        from panther.logger import logger
        logger.debug(f'Base Directory: {self.base_dir}')

        # Check Configs
        self.check_configs()
        config['debug'] = self.settings.get('DEBUG', config['debug'])
        config['default_cache_exp'] = self.settings.get('DEFAULT_CACHE_EXP', config['default_cache_exp'])
        config['secret_key'] = self.settings.get('SECRET_KEY', config['secret_key'])
        config['authentication'] = self.settings.get('Authentication', config['authentication'])
        # TODO: Only call this if Authentication is with JWT
        config['jwt_config'] = self.load_jwt_config()
        config['middlewares'] = self.load_middlewares()
        config['user_model'] = self.load_user_model()

        # Check & Collect URLs
        #   check_urls should be the last call in load_configs, because it will read all files and load them.
        urls = self.check_urls() or {}
        self.collect_urls('', urls)
        logger.debug('Configs Loaded.')

    def load_jwt_config(self) -> JWTConfig:
        user_config = self.settings.get('JWTConfig')
        return JWTConfig(**user_config) if user_config else JWTConfig(key=config['secret_key'])

    def check_configs(self):
        from panther.logger import logger

        try:
            configs_path = self.base_dir / 'core/configs.py'
            self.settings = run_path(str(configs_path))
        except FileNotFoundError:
            logger.critical('core/configs.py Not Found.')

    def check_urls(self) -> dict | None:
        from panther.logger import logger

        # URLs
        if self.settings.get('URLs') is None:
            return logger.critical("configs.py Does Not Have 'URLs'")

        urls_path = self.settings['URLs']
        try:
            full_urls_path = self.base_dir / urls_path
            urls_dict = run_path(str(full_urls_path))['urls']
        except FileNotFoundError:
            return logger.critical("Couldn't Open 'URLs' Address.")
        except KeyError:
            return logger.critical("'URLs' Address Does Not Have 'urls'")
        if not isinstance(urls_dict, dict):
            return logger.critical("'urls' Of URLs Is Not dict.")
        return urls_dict

    def collect_urls(self, pre_url, urls):
        from panther.logger import logger

        for url, endpoint in urls.items():
            if endpoint is ...:
                logger.error(f"URL Can't Point To Ellipsis. ('{pre_url}{url}' -> ...)")
            if endpoint is None:
                logger.error(f"URL Can't Point To None. ('{pre_url}{url}' -> None)")

            if isinstance(endpoint, dict):
                self.collect_urls(f'{pre_url}/{url}', endpoint)
            else:
                config['urls'][f'{pre_url}{url}'] = endpoint
        return urls

    def load_middlewares(self) -> list:
        from panther.logger import logger
        middlewares = list()

        for path, data in self.settings.get('Middlewares', []):
            if path.find('panther.middlewares.db.Middleware') != -1:
                config['db_engine'] = data['url'].split(':')[0]

            # noinspection PyPep8Naming
            Middleware = import_class(path)
            if not issubclass(Middleware, BaseMiddleware):
                logger.critical(f'{Middleware} is not a sub class of BaseMiddleware.')
                continue
            # noinspection PyArgumentList
            middlewares.append(Middleware(**data))
        return middlewares

    def find_endpoint(self, path):
        # TODO: Fix it later, it does not support root url or something like ''
        for url in config['urls']:
            if path == url:
                return config['urls'][url]
