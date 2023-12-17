from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.request import Request
from panther.test import APIClient


@API()
async def request_header(request: Request):
    return request.headers.__dict__


@API()
async def request_path(request: Request):
    return request.path


@API()
async def request_client(request: Request):
    return request.client


@API()
async def request_query_params(request: Request):
    return request.query_params


@API()
async def request_data(request: Request):
    return request.data


urls = {
    'request-header': request_header,
    'request-path': request_path,
    'request-client': request_client,
    'request-query_params': request_query_params,
    'request-data': request_data,
}


class TestSimpleRequests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def test_header(self):
        res = self.client.get('request-header/')
        assert res.status_code == 200
        headers = [
            'accept_encoding',
            'content_length',
            'authorization',
            'content_type',
            'user_agent',
            'connection',
            'accept',
            'host',
            'sec_websocket_version',
            'sec_websocket_key',
            'upgrade',
        ]
        assert [*res.data.keys()] == headers
        assert not all(res.data.values())

    def test_path(self):
        res = self.client.get('request-path/')
        assert res.status_code == 200
        assert res.data == '/request-path/'

    def test_client(self):
        res = self.client.get('request-client/')
        assert res.status_code == 200
        assert res.data == ['127.0.0.1', 8585]

    def test_query_params(self):
        res = self.client.get(
            'request-query_params/',
            query_params={'my': 'name', 'is': 'ali', 'how': 'are'},
        )
        assert res.status_code == 200
        assert res.data == {'my': 'name', 'is': 'ali', 'how': 'are'}
