from main import app
from panther.test import APIClient
from unittest import TestCase


class Test1(TestCase):

    def test1(self):
        client = APIClient(app=app)
        x = client.get('user/none-class/')
        print(f'{x.status_code=}')
        print(f'{x._data=}')

        assert True

    def test2(self):
        client = APIClient(app=app)
        x = client.get('user/none-class/')
        print(f'{x.status_code=}')
        print(f'{x._data=}')

        assert True

    def test3(self):
        client = APIClient(app=app)
        x = client.get('user/none-class/')
        print(f'{x.status_code=}')
        print(f'{x._data=}')

        assert True
