from concurrent.futures import ProcessPoolExecutor

import anyio

from panther.configs import config
from panther.utils import read_body, send_404, send_405, send_204
from panther.exceptions import APIException
from panther.response import Response
from panther.request import Request
from panther.logger import logger
from runpy import run_path
from pathlib import Path
from importlib import import_module


class Panther:

    def __init__(self, name):
        import os
        os.system('clear')
        self.base_dir = Path(name).resolve().parent
        self.panther_dir = Path(__file__).parent
        self.load_configs()
        del os

    async def run(self, scope, receive, send):
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

        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)

        # Call 'Before' Middlewares
        for middleware in config['middlewares']:
            request = await middleware.before(request=request)

        # Call Endpoint
        try:
            response = await endpoint(request=request)
        except APIException as e:
            response = Response(data=e.detail, status_code=e.status_code)
        if not isinstance(response, Response):
            return logger.error(f"Response Should Be Instance Of 'Response'.")

        # Call 'After' Middleware
        config['middlewares'].reverse()
        for middleware in config['middlewares']:
            response = await middleware.after(response=response)

        # Return Response
        if response._data is None or response.status_code == 204:
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

    def load_configs(self) -> None:
        logger.debug(f'Base Directory: {self.base_dir}')

        # Check Configs
        self.check_configs()
        config['debug'] = self.settings.get('DEBUG', config['debug'])

        # Collect Middlewares
        self.collect_middlewares()
        # Check & Collect URLs
        # check_urls should be the last call in load_configs, because it will read all files and load them.
        urls = self.check_urls()
        self.collect_urls('', urls)
        logger.debug('Configs Loaded.')

    def check_configs(self):
        try:
            configs_path = self.base_dir / 'core/configs.py'
            self.settings = run_path(str(configs_path))
        except FileNotFoundError:
            return logger.critical('core/configs.py Not Found.')

        # URLs
        if 'URLs' not in self.settings:
            return logger.critical("configs.py Does Not Have 'URLs'")

    def check_urls(self) -> dict:
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
        # TODO: use importlib
        # TODO: is sub instance of BaseMiddleware
        _middlewares = self.settings['Middlewares']
        for _middleware in _middlewares:
            if _middleware[0].split('/')[0] == 'panther':
                _middleware_name = _middleware[0].split('/')[-1]
                if _middleware_name == 'db.py':
                    config['db_engine'] = _middleware[1]['url'].split(':')[0]
                    from panther.middlewares.db import Middleware
                elif _middleware_name == 'redis.py':
                    from panther.middlewares.redis import Middleware
                else:
                    logger.error(f'{_middleware[0]} Does Not Found.')
                    continue
            else:
                # TODO: Import From Example (Custom Middleware)
                ...

            config['middlewares'].append(Middleware(**_middleware[1]))

    def find_endpoint(self, path):
        # TODO: Fix it later, it does not support root url or something like ''
        for url in config['urls']:
            if path == url:
                return config['urls'][url]
