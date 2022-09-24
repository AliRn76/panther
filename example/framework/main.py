from framework.exceptions import APIException
from framework.response import Response
from framework.request import Request
from framework.logger import logger
from pathlib import Path


class Framework:

    def load_configs(self) -> None:
        logger.debug(f'Base Directory: {self.base_dir}')

        try:
            from runpy import run_path
            logger.debug('Loading Configs ...')
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
        import os
        os.system('clear')
        self.base_dir = Path(name).resolve().parent
        self.load_configs()

    def find_endpoint(self, path):
        for url in self.urls:
            if path == url:
                return self.urls[url]

    @classmethod
    async def _404(cls, send):
        # TODO: Work On This Func
        await send({
            'type': 'http.response.start',
            'status': 404,
            'headers': [
                [b'content-type', b'application/json'],
            ],
        })
        return await send({
            'type': 'http.response.body',
            'body': b'',
        })

    @classmethod
    async def read_body(cls, receive):
        """
        Read and return the entire body from an incoming ASGI message.
        """
        body = b''
        more_body = True

        while more_body:
            message = await receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)

        return body

    async def __call__(self, scope, receive, send) -> None:
        # Find Endpoint
        endpoint = self.find_endpoint(path=scope['path'])
        if endpoint is None:
            return await self._404(send)

        # Check Endpoint Method
        endpoint_method = str(endpoint).split('.')[1].upper()
        if endpoint_method != scope['method']:
            return await self._404(send)

        # Read Body & Create Request
        body = await self.read_body(receive)
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




