import sys
from unittest import TestCase

from panther import Panther
from panther.test import APIClient


class TestSimpleRequests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/app')
        from tests.app.urls import simple_requests_urls

        app = Panther(__name__, configs=__name__, urls=simple_requests_urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

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
