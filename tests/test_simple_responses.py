from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.response import Response
from panther.test import APIClient


@API()
async def return_nothing():
    pass


@API()
async def return_none():
    return None


@API()
async def return_dict():
    return {'detail': 'ok'}


@API()
async def return_list():
    return [1, 2, 3]


@API()
async def return_tuple():
    return 1, 2, 3, 4


@API()
async def return_response_none():
    return Response()


@API()
async def return_response_dict():
    return Response(data={'detail': 'ok'})


@API()
async def return_response_list():
    return Response(data=['car', 'home', 'phone'])


@API()
async def return_response_tuple():
    return Response(data=('car', 'home', 'phone', 'book'))


urls = {
    'nothing': return_nothing,
    'none': return_none,
    'dict': return_dict,
    'list': return_list,
    'tuple': return_tuple,
    'response-none': return_response_none,
    'response-dict': return_response_dict,
    'response-list': return_response_list,
    'response-tuple': return_response_tuple,
}


class TestSimpleResponses(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def test_nothing(self):
        res = self.client.get('nothing/')
        assert res.status_code == 200
        assert res.data is None

    def test_none(self):
        res = self.client.get('none/')
        assert res.status_code == 200
        assert res.data is None

    def test_dict(self):
        res = self.client.get('dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}

    def test_list(self):
        res = self.client.get('list/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3]

    def test_tuple(self):
        res = self.client.get('tuple/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3, 4]

    def test_response_none(self):
        res = self.client.get('response-none/')
        assert res.status_code == 200
        assert res.data is None

    def test_response_dict(self):
        res = self.client.get('response-dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}

    def test_response_list(self):
        res = self.client.get('response-list/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone']

    def test_response_tuple(self):
        res = self.client.get('response-tuple/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone', 'book']
