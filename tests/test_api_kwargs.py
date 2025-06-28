from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API, GenericAPI
from panther.configs import config
from panther.request import Request
from panther.test import APIClient


@API()
async def request_api(request: Request):
    assert isinstance(request, Request)
    return True


@API()
async def req_api(req: Request):
    assert isinstance(req, Request)
    return True


@API()
async def integer_path_api(age: int):
    assert isinstance(age, int)
    return age


@API()
async def boolean_path_api(is_alive: bool):
    assert isinstance(is_alive, bool)
    return is_alive


@API()
async def string_path_api(name: str):
    assert isinstance(name, str)
    return name


@API()
async def unknown_path_api(subject):
    assert isinstance(subject, str)
    return subject


@API()
async def all_kwargs_api(request: Request, is_alive: bool, age: int, name: str, subject):
    assert isinstance(request, Request)
    assert isinstance(is_alive, bool)
    assert isinstance(age, int)
    assert isinstance(name, str)
    assert isinstance(subject, str)
    return is_alive, age, name, subject


@API()
async def unordered_kwargs_api(subject, is_alive: bool, name: str, request: Request, age: int):
    assert isinstance(request, Request)
    assert isinstance(is_alive, bool)
    assert isinstance(age, int)
    assert isinstance(name, str)
    assert isinstance(subject, str)
    return is_alive, age, name, subject


class AllKwargsAPI(GenericAPI):
    async def get(self, request: Request, is_alive: bool, age: int, name: str, subject):
        assert isinstance(request, Request)
        assert isinstance(is_alive, bool)
        assert isinstance(age, int)
        assert isinstance(name, str)
        assert isinstance(subject, str)
        return is_alive, age, name, subject


urls = {
    'request': request_api,
    'req': req_api,
    'integer/<age>/': integer_path_api,
    'boolean/<is_alive>/': boolean_path_api,
    'string/<name>/': string_path_api,
    'unknown/<subject>/': unknown_path_api,
    'all/<is_alive>/<age>/<name>/<subject>/': all_kwargs_api,
    'unordered/<is_alive>/<age>/<name>/<subject>/': unordered_kwargs_api,
    'class/<is_alive>/<age>/<name>/<subject>/': AllKwargsAPI,
}


class TestKwargs(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_request(self):
        res = await self.client.get('request')
        assert res.status_code == 200

    async def test_req(self):
        """Make sure it check the type of kwargs not the name of variable"""
        res = await self.client.get('req')
        assert res.status_code == 200

    async def test_integer(self):
        res = await self.client.get('integer/10/')
        assert res.status_code == 200
        assert res.data == 10

    async def test_invalid_integer(self):
        res = await self.client.get('integer/ali/')
        assert res.status_code == 400
        assert res.data == {'detail': 'Path variable `ali` is not `int`'}

    async def test_boolean_true(self):
        re1 = await self.client.get('boolean/true/')
        assert re1.status_code == 200
        assert re1.data == True

        res2 = await self.client.get('boolean/TRUE/')
        assert res2.status_code == 200
        assert res2.data == True

        res3 = await self.client.get('boolean/true/')
        assert res3.status_code == 200
        assert res3.data == True

    async def test_boolean_false(self):
        res1 = await self.client.get('boolean/false/')
        assert res1.status_code == 200
        assert res1.data == False

        res2 = await self.client.get('boolean/FALSE/')
        assert res2.status_code == 200
        assert res2.data == False

        res3 = await self.client.get('boolean/False/')
        assert res3.status_code == 200
        assert res3.data == False

        res4 = await self.client.get('boolean/0/')
        assert res4.status_code == 200
        assert res4.data == False

    async def test_invalid_boolean(self):
        res = await self.client.get('boolean/ali/')
        assert res.status_code == 400
        assert res.data == {'detail': 'Path variable `ali` is not `bool`'}

    async def test_string(self):
        res = await self.client.get('string/ali/')
        assert res.status_code == 200
        assert res.data == 'ali'

    async def test_unknown(self):
        res = await self.client.get('unknown/test/')
        assert res.status_code == 200
        assert res.data == 'test'

    async def test_all(self):
        res = await self.client.get('all/true/20/ali/test')
        assert res.status_code == 200
        assert res.data == [True, 20, 'ali', 'test']

    async def test_unordered(self):
        res = await self.client.get('unordered/true/20/ali/test')
        assert res.status_code == 200
        assert res.data == [True, 20, 'ali', 'test']

    async def test_class_based(self):
        res = await self.client.get('class/true/20/ali/test')
        assert res.status_code == 200
        assert res.data == [True, 20, 'ali', 'test']
