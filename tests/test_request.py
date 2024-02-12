from unittest import IsolatedAsyncioTestCase

import orjson as json

from panther import Panther
from panther.app import API, GenericAPI
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
async def request_path_variables(name: str, age: int, is_alive: bool):
    return {'name': name, 'age': age, 'is_alive': is_alive}


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
class AllMethods(GenericAPI):
    def get(self, *args, **kwargs):
        return Response()

    def post(self, *args, **kwargs):
        return Response()

    def put(self, *args, **kwargs):
        return Response()

    def patch(self, *args, **kwargs):
        return Response()

    def delete(self, *args, **kwargs):
        return Response()


@API()
async def all_methods():
    return Response()


class GetMethod(GenericAPI):
    def get(self, *args, **kwargs):
        return Response()


@API(methods=['GET'])
async def get_method():
    return Response()


class PostMethod(GenericAPI):
    def post(self, *args, **kwargs):
        return Response()


@API(methods=['POST'])
async def post_method():
    return Response()


class PutMethod(GenericAPI):
    def put(self, *args, **kwargs):
        return Response()


@API(methods=['PUT'])
async def put_method():
    return Response()


class PatchMethod(GenericAPI):
    def patch(self, *args, **kwargs):
        return Response()


@API(methods=['PATCH'])
async def patch_method():
    return Response()


class DeleteMethod(GenericAPI):
    def delete(self, *args, **kwargs):
        return Response()


@API(methods=['DELETE'])
async def delete_method():
    return Response()


class GetPostPatchMethods(GenericAPI):
    def get(self, *args, **kwargs):
        return Response()

    def post(self, *args, **kwargs):
        return Response()

    def patch(self, *args, **kwargs):
        return Response()


@API(methods=['GET', 'POST', 'PATCH'])
async def get_post_patch_methods():
    return Response()


urls = {
    'path': request_path,
    'client': request_client,
    'query-params': request_query_params,
    'data': request_data,
    'path/<name>/variable/<age>/<is_alive>/': request_path_variables,

    'header': request_header,
    'header-attr': request_header_by_attr,
    'header-item': request_header_by_item,

    'all-func': all_methods,
    'all-class': AllMethods,
    'get-func': get_method,
    'get-class': GetMethod,
    'post-func': post_method,
    'post-class': PostMethod,
    'put-func': put_method,
    'put-class': PutMethod,
    'patch-func': patch_method,
    'patch-class': PatchMethod,
    'delete-func': delete_method,
    'delete-class': DeleteMethod,
    'get-post-patch-func': get_post_patch_methods,
    'get-post-patch-class': GetPostPatchMethods,
}


class TestRequest(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    async def test_path(self):
        res = await self.client.get('path/')
        assert res.status_code == 200
        assert res.data == '/path/'

    async def test_client(self):
        res = await self.client.get('client/')
        assert res.status_code == 200
        assert res.data == ['127.0.0.1', 8585]

    async def test_query_params(self):
        res = await self.client.get(
            'query-params/',
            query_params={'my': 'name', 'is': 'ali', 'how': 'are'},
        )
        assert res.status_code == 200
        assert res.data == {'my': 'name', 'is': 'ali', 'how': 'are'}

    async def test_data(self):
        payload = {'detail': 'ok'}
        res = await self.client.post('data/', payload=json.dumps(payload))
        assert res.status_code == 200
        assert res.data == payload

    async def test_path_variables(self):
        res = await self.client.post('path/Ali/variable/27/true/')
        expected_response = {'name': 'Ali', 'age': 27, 'is_alive': True}
        assert res.status_code == 200
        assert res.data == expected_response

    # # # Headers
    async def test_headers_none(self):
        res = await self.client.get('header')
        expected_headers = {}
        assert res.data == expected_headers

    async def test_headers_content_type(self):
        res = await self.client.post('header')
        expected_headers = {'content-type': 'application/json'}
        assert res.data == expected_headers

    async def test_headers_full_items(self):
        headers = {
            'User-Agent': 'PostmanRuntime/7.36.0',
            'Accept': '*/*',
            'Cache-Control': 'no-cache',
            'Host': '127.0.0.1:8000',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': 546,
        }
        res = await self.client.post('header', headers=headers)
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

    async def test_headers_unknown_items(self):
        headers = {
            'Header1': 'PostmanRuntime/7.36.0',
            'Header2': '*/*',
        }
        res = await self.client.post('header', headers=headers)
        expected_headers = {
            'content-type': 'application/json',
            'Header1': 'PostmanRuntime/7.36.0',
            'Header2': '*/*',
        }
        assert res.data == expected_headers

    async def test_headers_authorization_by_getattr(self):
        headers = {
            'Authorization': 'Token xxx',
        }
        res = await self.client.post('header-attr', headers=headers)
        assert res.data == 'Token xxx'

    async def test_headers_authorization_by_getitem(self):
        headers = {
            'Authorization': 'Token xxx',
        }
        res = await self.client.post('header-item', headers=headers)
        assert res.data == 'Token xxx'

    # # # Methods
    async def test_method_all(self):
        res_func = await self.client.get('all-func/')
        res_class = await self.client.get('all-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.post('all-func/')
        res_class = await self.client.post('all-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.put('all-func/')
        res_class = await self.client.put('all-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.patch('all-func/')
        res_class = await self.client.patch('all-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.delete('all-func/')
        res_class = await self.client.delete('all-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

    async def test_method_get(self):
        res_func = await self.client.get('get-func/')
        res_class = await self.client.get('get-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.post('get-func/')
        res_class = await self.client.post('get-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.put('get-func/')
        res_class = await self.client.put('get-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.patch('get-func/')
        res_class = await self.client.patch('get-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.delete('get-func/')
        res_class = await self.client.delete('get-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

    async def test_method_post(self):
        res_func = await self.client.get('post-func/')
        res_class = await self.client.get('post-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.post('post-func/')
        res_class = await self.client.post('post-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.put('post-func/')
        res_class = await self.client.put('post-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.patch('post-func/')
        res_class = await self.client.patch('post-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.delete('post-func/')
        res_class = await self.client.delete('post-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

    async def test_method_put(self):
        res_func = await self.client.get('put-func/')
        res_class = await self.client.get('put-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.post('put-func/')
        res_class = await self.client.post('put-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.put('put-func/')
        res_class = await self.client.put('put-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.patch('put-func/')
        res_class = await self.client.patch('put-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.delete('put-func/')
        res_class = await self.client.delete('put-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

    async def test_method_patch(self):
        res_func = await self.client.get('patch-func/')
        res_class = await self.client.get('patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.post('patch-func/')
        res_class = await self.client.post('patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.put('patch-func/')
        res_class = await self.client.put('patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.patch('patch-func/')
        res_class = await self.client.patch('patch-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.delete('patch-func/')
        res_class = await self.client.delete('patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

    async def test_method_delete(self):
        res_func = await self.client.get('delete-func/')
        res_class = await self.client.get('delete-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.post('delete-func/')
        res_class = await self.client.post('delete-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.put('delete-func/')
        res_class = await self.client.put('delete-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.patch('delete-func/')
        res_class = await self.client.patch('delete-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.delete('delete-func/')
        res_class = await self.client.delete('delete-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

    async def test_method_get_post_patch(self):
        res_func = await self.client.get('get-post-patch-func/')
        res_class = await self.client.get('get-post-patch-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.post('get-post-patch-func/')
        res_class = await self.client.post('get-post-patch-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.put('get-post-patch-func/')
        res_class = await self.client.put('get-post-patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405

        res_func = await self.client.patch('get-post-patch-func/')
        res_class = await self.client.patch('get-post-patch-class/')
        assert res_func.status_code == 200
        assert res_class.status_code == 200

        res_func = await self.client.delete('get-post-patch-func/')
        res_class = await self.client.delete('get-post-patch-class/')
        assert res_func.status_code == 405
        assert res_class.status_code == 405
