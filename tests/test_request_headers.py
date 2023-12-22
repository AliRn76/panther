from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.request import Request
from panther.response import Response
from panther.test import APIClient


@API()
async def simple_api(request: Request):
    return Response(request.headers.__dict__)


urls = {
    'simple': simple_api,
}


class TestHeaders(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def test_none(self):
        res = self.client.get('simple')
        expected_headers = {
            'accept_encoding': None,
            'content_length': None,
            'authorization': None,
            'content_type': None,
            'user_agent': None,
            'connection': None,
            'accept': None,
            'host': None,
            'sec_websocket_version': None,
            'sec_websocket_key': None,
            'upgrade': None
        }
        assert res.data == expected_headers

    def test_content_type(self):
        res = self.client.post('simple')
        expected_headers = {
            'accept_encoding': None,
            'content_length': None,
            'authorization': None,
            'content_type': 'application/json',
            'user_agent': None,
            'connection': None,
            'accept': None,
            'host': None,
            'sec_websocket_version': None,
            'sec_websocket_key': None,
            'upgrade': None
        }
        assert res.data == expected_headers

    def test_full_headers(self):
        headers = {
            'User-Agent': 'PostmanRuntime/7.36.0',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Host': '127.0.0.1:8000',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': 546,
        }
        res = self.client.post('simple', headers=headers)

        expected_headers = {
            'accept_encoding': 'gzip, deflate, br',
            'content_length': '546',
            'authorization': None,
            'content_type': 'application/json',
            'user_agent': 'PostmanRuntime/7.36.0',
            'connection': 'keep-alive',
            'accept': '*/*',
            'host': '127.0.0.1:8000',
            'sec_websocket_version': None,
            'sec_websocket_key': None,
            'upgrade': None,
        }
        assert res.data == expected_headers
