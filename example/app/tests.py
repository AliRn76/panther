from unittest import TestCase

from main import app

from panther.test import APIClient


class Test1(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = APIClient(app=app)

    def test_none_class(self):
        res = self.client.get('user/none-class/')
        assert res.status_code == 200
        assert res.data is None

    def test_none(self):
        res = self.client.get('user/none/')
        assert res.status_code == 200
        assert res.data is None

    def test_dict(self):
        res = self.client.get('user/dict/')
        assert res.status_code == 200
        breakpoint()
        assert res.data == {'detail': 'ok'}
