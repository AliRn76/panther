import sys
from panther.test import APIClient
from unittest import TestCase


class TestSimpleResponses(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        sys.path.append('tests/app')
        from tests.app.main import app
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.pop()

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
