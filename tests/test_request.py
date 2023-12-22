from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.request import Request
from panther.response import Response
from panther.test import APIClient


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


@API()
async def request_header(request: Request):
    return request.headers.__dict__


@API()
async def request_header_by_attr(request: Request):
    return request.headers.authorization


@API()
async def request_header_by_item(request: Request):
    return request.headers['Authorization']


# # # Methods
@API()
async def request_all():
    return Response()


@API(methods=['GET'])
async def request_get():
    return Response()


@API(methods=['POST'])
async def request_post():
    return Response()


@API(methods=['PUT'])
async def request_put():
    return Response()


@API(methods=['PATCH'])
async def request_patch():
    return Response()


@API(methods=['DELETE'])
async def request_delete():
    return Response()


@API(methods=['GET', 'POST', 'PATCH'])
async def request_get_post_patch():
    return Response()


urls = {
    'request-header': request_header,
    'request-header-attr': request_header_by_attr,
    'request-header-item': request_header_by_item,
    'request-path': request_path,
    'request-client': request_client,
    'request-query_params': request_query_params,
    'request-data': request_data,
    'all': request_all,
    'get': request_get,
    'post': request_post,
    'put': request_put,
    'patch': request_patch,
    'delete': request_delete,
    'get-post-patch': request_get_post_patch,
}


class TestRequest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

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

    # # # Headers
    def test_headers_none(self):
        res = self.client.get('request-header')
        expected_headers = {}
        assert res.data == expected_headers

    def test_headers_content_type(self):
        res = self.client.post('request-header')
        expected_headers = {'content-type': 'application/json'}
        assert res.data == expected_headers

    def test_headers_full_items(self):
        headers = {
            'User-Agent': 'PostmanRuntime/7.36.0',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Host': '127.0.0.1:8000',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': 546,
        }
        res = self.client.post('request-header', headers=headers)
        expected_headers = {
            'content-type': 'application/json',
            'User-Agent': 'PostmanRuntime/7.36.0',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Host': '127.0.0.1:8000',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': '546',
        }
        assert res.data == expected_headers

    def test_headers_unknown_items(self):
        headers = {
            'Header1': 'PostmanRuntime/7.36.0',
            'Header2': '*/*',
        }
        res = self.client.post('request-header', headers=headers)
        expected_headers = {
            'content-type': 'application/json',
            'Header1': 'PostmanRuntime/7.36.0',
            'Header2': '*/*',
        }
        assert res.data == expected_headers

    def test_headers_authorization_by_getattr(self):
        headers = {
            'Authorization': 'Token xxx',
        }
        res = self.client.post('request-header-attr', headers=headers)
        assert res.data == 'Token xxx'

    def test_headers_authorization_by_getitem(self):
        headers = {
            'Authorization': 'Token xxx',
        }
        res = self.client.post('request-header-item', headers=headers)
        assert res.data == 'Token xxx'

    # # # Methods
    def test_method_all(self):
        res = self.client.get('all/')
        assert res.status_code == 200

        res = self.client.post('all/')
        assert res.status_code == 200

        res = self.client.put('all/')
        assert res.status_code == 200

        res = self.client.patch('all/')
        assert res.status_code == 200

        res = self.client.delete('all/')
        assert res.status_code == 200

    def test_method_get(self):
        res = self.client.get('get/')
        assert res.status_code == 200

        res = self.client.post('get/')
        assert res.status_code == 405

        res = self.client.put('get/')
        assert res.status_code == 405

        res = self.client.patch('get/')
        assert res.status_code == 405

        res = self.client.delete('get/')
        assert res.status_code == 405

    def test_method_post(self):
        res = self.client.get('post/')
        assert res.status_code == 405

        res = self.client.post('post/')
        assert res.status_code == 200

        res = self.client.put('post/')
        assert res.status_code == 405

        res = self.client.patch('post/')
        assert res.status_code == 405

        res = self.client.delete('post/')
        assert res.status_code == 405

    def test_method_put(self):
        res = self.client.get('put/')
        assert res.status_code == 405

        res = self.client.post('put/')
        assert res.status_code == 405

        res = self.client.put('put/')
        assert res.status_code == 200

        res = self.client.patch('put/')
        assert res.status_code == 405

        res = self.client.delete('put/')
        assert res.status_code == 405

    def test_method_patch(self):
        res = self.client.get('patch/')
        assert res.status_code == 405

        res = self.client.post('patch/')
        assert res.status_code == 405

        res = self.client.put('patch/')
        assert res.status_code == 405

        res = self.client.patch('patch/')
        assert res.status_code == 200

        res = self.client.delete('patch/')
        assert res.status_code == 405

    def test_method_delete(self):
        res = self.client.get('delete/')
        assert res.status_code == 405

        res = self.client.post('delete/')
        assert res.status_code == 405

        res = self.client.put('delete/')
        assert res.status_code == 405

        res = self.client.patch('delete/')
        assert res.status_code == 405

        res = self.client.delete('delete/')
        assert res.status_code == 200

    def test_method_get_post_patch(self):
        res = self.client.get('get-post-patch/')
        assert res.status_code == 200

        res = self.client.post('get-post-patch/')
        assert res.status_code == 200

        res = self.client.put('get-post-patch/')
        assert res.status_code == 405

        res = self.client.patch('get-post-patch/')
        assert res.status_code == 200

        res = self.client.delete('get-post-patch/')
        assert res.status_code == 405
