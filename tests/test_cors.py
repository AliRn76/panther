from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API
from panther.configs import config
from panther.test import APIClient


@API()
async def simple_api():
    return {'detail': 'ok'}


urls = {'test': simple_api}

ALLOW_ORIGINS = ['*']
ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
ALLOW_HEADERS = ['*']
ALLOW_CREDENTIALS = False
EXPOSE_HEADERS = []
CORS_MAX_AGE = 600
MIDDLEWARES = ['panther.middlewares.cors.CORSMiddleware']


class TestCORSMiddlewares(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        config.refresh()

    async def test_default_cors_headers(self):
        allow_origins = config.ALLOW_ORIGINS
        allow_methods = config.ALLOW_METHODS
        allow_headers = config.ALLOW_HEADERS
        allow_credentials = config.ALLOW_CREDENTIALS
        expose_headers = config.EXPOSE_HEADERS
        res = await self.client.get(path='test', headers={'origin': 'http://example.com'})
        assert res.status_code == 200
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Access-Control-Allow-Methods'] == ', '.join(ALLOW_METHODS)
        assert res.headers['Access-Control-Allow-Headers'] == ', '.join(ALLOW_HEADERS)
        assert res.headers['Access-Control-Max-Age'] == str(CORS_MAX_AGE)
        assert 'Access-Control-Allow-Credentials' not in res.headers
        assert 'Access-Control-Expose-Headers' not in res.headers
        config.ALLOW_ORIGINS = allow_origins
        config.ALLOW_METHODS = allow_methods
        config.ALLOW_HEADERS = allow_headers
        config.ALLOW_CREDENTIALS = allow_credentials
        config.EXPOSE_HEADERS = expose_headers

    async def test_preflight_options(self):
        res = await self.client.options(path='test', headers={'origin': 'http://example.com'})
        assert res.status_code == 204
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Access-Control-Allow-Methods'] == ', '.join(ALLOW_METHODS)
        assert res.headers['Access-Control-Allow-Headers'] == ', '.join(ALLOW_HEADERS)
        assert res.headers['Access-Control-Max-Age'] == str(CORS_MAX_AGE)

    async def test_custom_origins(self):
        allow_origins = config.ALLOW_ORIGINS
        config.ALLOW_ORIGINS = ['https://allowed.com']
        res = await self.client.get(path='test', headers={'origin': 'https://allowed.com'})
        assert res.headers['Access-Control-Allow-Origin'] == 'https://allowed.com'
        res = await self.client.get(path='test', headers={'origin': 'https://not-allowed.com'})
        assert res.headers['Access-Control-Allow-Origin'] == 'https://allowed.com'
        config.ALLOW_ORIGINS = allow_origins

    async def test_credentials(self):
        allow_credentials = config.ALLOW_CREDENTIALS
        config.ALLOW_CREDENTIALS = True
        res = await self.client.get(path='test', headers={'origin': 'http://example.com'})
        assert res.headers['Access-Control-Allow-Credentials'] == 'true'
        config.ALLOW_CREDENTIALS = allow_credentials

    async def test_expose_headers(self):
        expose_headers = config.EXPOSE_HEADERS
        config.EXPOSE_HEADERS = ['X-My-Header', 'X-Another-Header']
        res = await self.client.get(path='test', headers={'origin': 'http://example.com'})
        assert res.headers['Access-Control-Expose-Headers'] == 'X-My-Header, X-Another-Header'
        config.EXPOSE_HEADERS = expose_headers
