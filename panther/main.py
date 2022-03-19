from panther.db.connection import create_session
from panther.database import SupportedDatabase
from panther.utils import read_body, send_404
from panther.exceptions import APIException
from panther.response import Response
from panther.request import Request
from panther.logger import logger
from pathlib import Path


class Panther:

    def __init__(self, name):
        import os
        os.system('clear')
        del os
        self.base_dir = Path(name).resolve().parent
        self.load_configs()

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
        # Call Endpoint
        try:
            response = await endpoint(request=request)
        except APIException as e:
            response = Response(data=e.detail, status_code=e.status_code)
        if not isinstance(response, Response):
            return logger.error(f"Response Should Be Instance Of 'Response'.")
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

    def load_configs(self) -> None:
        logger.debug(f'Base Directory: {self.base_dir}')

        try:
            from runpy import run_path
            logger.debug('Loading Configs ...')
            urls_path = self.base_dir / 'core/configs.py'
            self.settings = run_path(str(urls_path))
        except FileNotFoundError:
            return logger.critical('core/configs.py Not Found.')
        finally:
            del run_path

        # Check Configs
        self.check_configs()

        # Set Configs
        self.urls = {}
        self.collect_urls('', self.settings['URLs'])
        self.debug = self.settings.get('DEBUG', False)
        self.set_database_url()

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

    def set_database_url(self):
        config = self.settings['DatabaseConfig']
        db_type = config['DATABASE_TYPE']
        host = config.get('HOST', '127.0.0.1')
        port = config.get('PORT') or 3306 if db_type == 'MySQL' else 5432 if db_type == 'postgresql' else None
        username = config.get('USERNAME')
        password = config.get('PASSWORD')
        name = config.get('NAME')
        """sqlite+aiosqlite:///file_path"""
        # TODO: install aiosqlite if sqlite selected
        # self.database_url = f'{db_type.lower()}://{username}:{password}@{host}:{port}/{name}'
        self.database_url = f'sqlite+aiosqlite:///{name}'
        # DBSession(database_url=self.database_url, database_type=db_type)
        create_session(database_url=self.database_url, database_type=db_type)

    def find_endpoint(self, path):
        # TODO: Fix it later, it does not support root url or something like ''
        for url in self.urls:
            if path == url:
                return self.urls[url]






