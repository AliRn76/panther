# from panther.db.connection import create_session
from panther.database import SupportedDatabase
from panther.utils import read_body, send_404
from panther.exceptions import APIException
from panther.response import Response
from panther.request import Request
from panther.logger import logger
from runpy import run_path
from pathlib import Path


class Panther:

    def __init__(self, name):
        import os
        os.system('clear')
        self.base_dir = Path(name).resolve().parent
        # TODO: Fix self.panther_dir
        self.panther_dir = f"{os.environ['VIRTUAL_ENV']}/lib/python3.10/site-packages/panther"
        self.load_configs()
        del os

    async def __call__(self, scope, receive, send) -> None:
        # Find Endpoint
        endpoint = self.find_endpoint(path=scope['path'])
        if endpoint is None:
            return await send_404(send)

        # Check Endpoint Method
        endpoint_method = str(endpoint).split('.')[1].upper()
        if endpoint_method != scope['method']:
            return await send_404(send)

        # Read Body & Create Request
        body = await read_body(receive)
        request = Request(scope=scope, body=body)

        setattr(request, 'db_url', self.db_url())  # TODO: I think this is not the best place for db_url ?(
        # Call Before Middlewares
        for middleware in self.middlewares:
            request = await middleware.before(request=request)

        # Call Endpoint
        try:
            response = await endpoint(request=request)
        except APIException as e:
            response = Response(data=e.detail, status_code=e.status_code)
        if not isinstance(response, Response):
            return logger.error(f"Response Should Be Instance Of 'Response'.")

        # Call After Middleware
        self.middlewares.reverse()
        for middleware in self.middlewares:
            response = await middleware.after(response=response)

        # Return Response
        await send({
            'type': 'http.response.start',
            'status': response.status_code,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': response.data,
        })

    def load_configs(self) -> None:
        logger.debug(f'Base Directory: {self.base_dir}')

        try:
            logger.debug('Loading Configs ...')
            configs_path = self.base_dir / 'core/configs.py'
            self.settings = run_path(str(configs_path))
        except FileNotFoundError:
            return logger.critical('core/configs.py Not Found.')

        # Check Configs
        self.check_configs()
        self.debug = self.settings.get('DEBUG', False)

        # Check & Collect URLs
        urls = self.check_urls()
        self.urls = {}
        self.collect_urls('', urls)

        # Collect Middlewares
        self.middlewares = []
        self.collect_middlewares()

    def check_configs(self):
        # URLs
        if 'URLs' not in self.settings:
            return logger.critical("configs.py Does Not Have 'URLs'")

        # DB
        if 'DatabaseConfig' not in self.settings:
            return logger.critical("configs.py Does Not Have 'DatabaseConfig'")
        if 'DATABASE_TYPE' not in self.settings['DatabaseConfig']:
            return logger.critical("'DatabaseConfig' Does Not Have 'DATABASE'")
        if self.settings['DatabaseConfig']['DATABASE_TYPE'] not in SupportedDatabase:
            return logger.critical("'DATABASE_TYPE' Is Not In 'SupportedDatabase'")

    def check_urls(self) -> dict:
        urls_path = self.settings['URLs']
        try:
            full_urls_path = self.base_dir / urls_path
            urls_dict = run_path(str(full_urls_path))['urls']
        except FileNotFoundError:
            return logger.critical("Could Open 'URLs' Address.")
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
                self.urls[f'{pre_url}{url}'] = endpoint
        return urls

    def collect_middlewares(self):
        # TODO: is sub instance of BaseMiddleware
        _middlewares = self.settings['Middlewares']
        _first_middleware_path = _middlewares[0]
        if _first_middleware_path.split('/')[-1] == 'db.py':
            from panther.middlewares.db import Middleware as db_middleware
            self.middlewares.append(db_middleware())

    def db_url(self) -> str:
        config = self.settings['DatabaseConfig']
        db_type = config['DATABASE_TYPE']
        host = config.get('HOST', '127.0.0.1')
        port = config.get('PORT') or 3306 if db_type == 'MySQL' else 5432 if db_type == 'postgresql' else None
        username = config.get('USERNAME')
        password = config.get('PASSWORD')
        name = config.get('NAME')
        if db_type == 'SQLite':
            return f'{db_type.lower()}:///{self.base_dir}/{name}.db'
        else:
            return f'{db_type.lower()}://{username}:{password}@{host}:{port}/{name}'

    def find_endpoint(self, path):
        # TODO: Fix it later, it does not support root url or something like ''
        for url in self.urls:
            if path == url:
                return self.urls[url]
