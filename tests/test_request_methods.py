from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.response import Response
from panther.test import APIClient


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
    'all': request_all,
    'get': request_get,
    'post': request_post,
    'put': request_put,
    'patch': request_patch,
    'delete': request_delete,
    'get-post-patch': request_get_post_patch,
}


class TestMethods(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def test_all(self):
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

    def test_get(self):
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

    def test_post(self):
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

    def test_put(self):
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

    def test_patch(self):
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

    def test_delete(self):
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

    def test_get_post_patch(self):
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
