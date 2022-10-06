import importlib

import anyio
from pathlib import Path
from runpy import run_path

from pydantic.main import ModelMetaclass

from panther.configs import config, JWTConfig
from panther.middlewares.base import BaseMiddleware
from panther.request import Request
from panther.response import Response
from panther.exceptions import APIException
from panther.utils import read_body, send_404, send_405, send_204, import_class

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

    async def run(self, scope, receive, send):
        from panther.logger import logger, monitoring
        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)
        # TODO: put user_ip, method to Request

        # TODO: put access_log to config

        # Access Log
        # TODO: use this log as a middleware so can have a response status too.
        #  ** (we should refactor the structure for this) **
        monitoring.info(f"[{scope['method']}] {scope['path']} | {scope['client'][0]}:{scope['client'][1]}")

        # TODO: pass request.path to find_endpoint instead of scope[]
        # Find Endpoint
        endpoint = self.find_endpoint(path=scope['path'])
        if endpoint is None:
            return await send_404(send)

        # Check Endpoint Method
        if endpoint.__module__ != 'panther.app':
            raise TypeError(f'You have to use API decorator on {endpoint.__module__}.{endpoint.__name__}()')
        endpoint_method = endpoint.__qualname__.split('.')[1].upper()
        if endpoint_method != scope['method']:
            return await send_405(send)

        try:
            # Call 'Before' Middlewares
            for middleware in config['middlewares']:
                request = await middleware.before(request=request)

            # Call Endpoint
            response = await endpoint(request=request)
        except APIException as e:
            response = self.handle_exceptions(e)

        # Call 'After' Middleware
        config['middlewares'].reverse()
        for middleware in config['middlewares']:
            try:
                response = await middleware.after(response=response)
            except APIException as e:
                response = self.handle_exceptions(e)

        # Return Response
        if (response._data is None and response.status_code == 200) or response.status_code == 204:
            return await send_204(send)

        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({'type': 'http.response.body', 'body': response.data})

    async def __call__(self, scope, receive, send) -> None:
        # await self.run(scope, receive, send)
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(self.run, scope, receive, send)
            # await anyio.to_thread.run_sync(self.run, scope, receive, send)
        # if self.exc_info is not None:
        #     raise self.exc_info[0].with_traceback(self.exc_info[1], self.exc_info[2])

        # with ProcessPoolExecutor() as e:
        #     e.submit(self.run, scope, receive, send)

    @classmethod
    def handle_exceptions(cls, e, /) -> Response:
        return Response(
            data=e.detail if isinstance(e.detail, dict) else {'detail': e.detail},
            status_code=e.status_code
        )

    def load_user_model(self) -> ModelMetaclass:
        return import_class(self.settings.get('USER_MODEL'))

    def load_configs(self) -> None:
        from panther.logger import logger
        logger.debug(f'Base Directory: {self.base_dir}')

        # Check Configs
        self.check_configs()
        config['debug'] = self.settings.get('DEBUG', config['debug'])
        config['default_cache_exp'] = self.settings.get('DEFAULT_CACHE_EXP', config['default_cache_exp'])
        config['secret_key'] = self.settings.get('SECRET_KEY', config['secret_key'])
        config['user_model'] = self.load_user_model()

        config['authentication'] = self.settings.get('Authentication', config['authentication'])
        # TODO: Only call this if Authentication is with JWT
        self.set_jwt_config()

        # Collect Middlewares
        self.collect_middlewares()
        # Check & Collect URLs
        #   check_urls should be the last call in load_configs, because it will read all files and load them.
        urls = self.check_urls()
        self.collect_urls('', urls)
        logger.debug('Configs Loaded.')

    def set_jwt_config(self):
        user_config = self.settings.get('JWTConfig')
        jwt_config = JWTConfig(**user_config) if user_config else JWTConfig(key=config['secret_key'])
        config['jwt_config'] = jwt_config

    def check_configs(self):
        from panther.logger import logger

        try:
            configs_path = self.base_dir / 'core/configs.py'
            self.settings = run_path(str(configs_path))
        except FileNotFoundError:
            return logger.critical('core/configs.py Not Found.')

        # URLs
        if 'URLs' not in self.settings:
            return logger.critical("configs.py Does Not Have 'URLs'")

    def check_urls(self) -> dict:
        from panther.logger import logger

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

    def collect_middlewares(self):
        from panther.logger import logger

        middlewares = self.settings['Middlewares']
        for path, data in middlewares:
            middleware = import_class(path)
            if hasattr(middleware, 'db_engine'):
                config['db_engine'] = middleware.db_engine

            if not issubclass(middleware, BaseMiddleware):
                logger.critical(f'{middleware} is not a sub class of BaseMiddleware.')
                continue

            config['middlewares'].append(middleware(**data))

    def find_endpoint(self, path):
        # TODO: Fix it later, it does not support root url or something like ''
        for url in config['urls']:
            if path == url:
                return config['urls'][url]
