from pathlib import Path
from framework.logger import logger

import orjson

class Framework:

    def load_configs(self) -> None:
        logger.debug(f'Base Directory: {self.base_dir}')

        try:
            from runpy import run_path
            logger.debug('Loading Configs')
            urls_path = self.base_dir / 'core/configs.py'
            settings = run_path(f'{urls_path}')
        except FileNotFoundError:
            return logger.critical('core/configs.py Not Found.')
        finally:
            del run_path

        # Check Configs
        if not settings.get('URLs'):
            return logger.critical('configs.py Does Not Have \'URLs\'')

        # Set Configs
        self.urls = {}
        self.set_urls('', settings['URLs'])
        self.debug = settings.get('DEBUG', False)

    def set_urls(self, pre_url, urls):
        for url, endpoint in urls.items():
            if endpoint is ...:
                logger.error(f"URL Can't Point To Ellipsis. ('{pre_url}{url}' -> ...)")
            if endpoint is None:
                logger.error(f"URL Can't Point To None. ('{pre_url}{url}' -> None)")

            if isinstance(endpoint, dict):
                self.set_urls(f'{pre_url}/{url}', endpoint)
            else:
                self.urls[f'{pre_url}{url}'] = endpoint
        return urls

    def __init__(self, name):
        self.base_dir = Path(name).resolve().parent
        self.load_configs()

    def find_endpoint(self, path):
        for url in self.urls:
            if path == url:
                return self.urls[url]

    async def __call__(self, scope, receive, send):
        assert scope['type'] == 'http'
        method = scope['method']
        path = scope['path']
        # print(f'{scope = }', end='\n\n')
        # print(f'{receive = }', end='\n\n')
        # print(f'{send = }', end='\n\n')
        # print(f'{self = }', end='\n\n')
        # print(f'{method = }', end='\n\n')
        # print(f'{path = }', end='\n\n')
        # print(f'{dir(self) = }', end='\n\n')
        # print(f'{self.__dict__ = }', end='\n\n')
        # print(f'{self.__doc__ = }', end='\n\n')
        # print(f'{self.__doc__ = }', end='\n\n')
        # print(f'{self.base_dir = }', end='\n\n')
        print(f'{self.urls = }', end='\n\n')
        endpoint = self.find_endpoint(path=path)
        print(f'{endpoint = }', end='\n\n')
        # TODO: check method exists?
        response = await endpoint('', body=receive)

        print(f'{response = }', end='\n\n')
        print(f'{type(response) = }', end='\n\n')
        if isinstance(response, tuple):
            # TODO: validate response type with specific class
            if isinstance(response[0], int):
                response_status_code = response[0]
            else:
                logger.error(f'Status Code Should Be Int. ({response[0]} -> {type(response[0])})')
                response_status_code = 400
            response_body = response[1]
        else:
            response_status_code = 200
            response_body = response

        await send({
            'type': 'http.response.start',
            'status': response_status_code,
            'headers': [
                [b'content-type', b'text/plain'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': orjson.dumps(response_body),
        })




