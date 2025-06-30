from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel

from panther import Panther
from panther.app import API, GenericAPI
from panther.configs import config
from panther.db import Model
from panther.response import Cookie, HTMLResponse, PlainTextResponse, Response, StreamingResponse, TemplateResponse
from panther.test import APIClient


@API()
async def return_nothing():
    pass


class ReturnNothing(GenericAPI):
    def get(self):
        pass


@API()
async def return_none():
    return None


class ReturnNone(GenericAPI):
    def get(self):
        return None


@API()
async def return_string():
    return 'Hello'


class ReturnString(GenericAPI):
    def get(self):
        return 'Hello'


@API()
async def return_dict():
    return {'detail': 'ok'}


class ReturnDict(GenericAPI):
    def get(self):
        return {'detail': 'ok'}


@API()
async def return_list():
    return [1, 2, 3]


class ReturnList(GenericAPI):
    def get(self):
        return [1, 2, 3]


@API()
async def return_tuple():
    return 1, 2, 3, 4


class ReturnTuple(GenericAPI):
    def get(self):
        return 1, 2, 3, 4


@API()
async def return_response_none():
    return Response()


class ReturnResponseNone(GenericAPI):
    def get(self):
        return Response()


@API()
async def return_response_dict():
    return Response(data={'detail': 'ok'})


class ReturnResponseDict(GenericAPI):
    def get(self):
        return Response(data={'detail': 'ok'})


@API()
async def return_response_list():
    return Response(data=['car', 'home', 'phone'])


class ReturnResponseList(GenericAPI):
    def get(self):
        return Response(data=['car', 'home', 'phone'])


@API()
async def return_response_tuple():
    return Response(data=('car', 'home', 'phone', 'book'))


class ReturnResponseTuple(GenericAPI):
    def get(self):
        return Response(data=('car', 'home', 'phone', 'book'))


class CustomUser(BaseModel):
    name: str
    age: int
    is_alive: bool


class CustomBook(BaseModel):
    title: str
    author: CustomUser
    readers: list[CustomUser]


class ReturnResponseBaseModel(GenericAPI):
    def get(self):
        return Response(data=CustomUser(name='John', age=21, is_alive=True))


class ReturnResponseNestedBaseModel(GenericAPI):
    def get(self):
        return Response(
            data={
                'name': 'Ali',
                'book': CustomBook(
                    title='Boo1',
                    author=CustomUser(name='John', age=21, is_alive=True),
                    readers=[
                        CustomUser(name='Sara', age=22, is_alive=True),
                        CustomUser(name='Sam', age=5, is_alive=False),
                    ],
                ),
                'user': CustomUser(name='Ali', age=2, is_alive=True),
                'books': [
                    CustomBook(title='Book1', author=CustomUser(name='John1', age=21, is_alive=True), readers=[]),
                    CustomBook(title='Book2', author=CustomUser(name='John2', age=22, is_alive=True), readers=[]),
                ],
            }
        )


class CustomProduct(Model):
    title: str


class ReturnResponseModel(GenericAPI):
    def get(self):
        return Response(data=CustomProduct(title='Fruit'))


@API()
async def return_html_response():
    return HTMLResponse('<html><head><title></title></head></html>')


class ReturnHTMLResponse(GenericAPI):
    def get(self):
        return HTMLResponse('<html><head><title></title></head></html>')


@API()
async def return_template_response() -> TemplateResponse:
    return TemplateResponse(source='<html><body><p>{{ content }}</p></body></html>', context={'content': 'Hello World'})


class ReturnTemplateResponse(GenericAPI):
    def get(self) -> TemplateResponse:
        return TemplateResponse(
            source='<html><body><p>{{ content }}</p></body></html>',
            context={'content': 'Hello World'},
        )


@API()
async def return_plain_response():
    return PlainTextResponse('Hello World')


class ReturnPlainResponse(GenericAPI):
    def get(self):
        return PlainTextResponse('Hello World')


class ReturnStreamingResponse(GenericAPI):
    def get(self):
        def f():
            yield from range(5)

        return StreamingResponse(f())


class ReturnAsyncStreamingResponse(GenericAPI):
    async def get(self):
        async def f():
            for i in range(6):
                yield i

        return StreamingResponse(f())


@API()
def full_cookie_api():
    return Response(
        set_cookies=Cookie(
            key='custom_key',
            value='custom_value',
            domain='example.com',
            max_age=100,
            secure=True,
            httponly=True,
            samesite='strict',
            path='/here/',
        )
    )


@API()
def multiple_cookies_api():
    return Response(
        set_cookies=[
            Cookie(
                key='custom_key1',
                value='custom_value1',
                domain='example.com',
                max_age=100,
                secure=True,
                httponly=True,
                samesite='strict',
                path='/here/',
            ),
            Cookie(
                key='custom_key2',
                value='custom_value2',
                domain='example.com',
                max_age=100,
                secure=True,
                httponly=True,
                samesite='strict',
                path='/here/',
            ),
        ]
    )


@API()
def default_cookies_api():
    return Response(set_cookies=Cookie(key='custom_key', value='custom_value'))


urls = {
    'nothing': return_nothing,
    'none': return_none,
    'dict': return_dict,
    'str': return_string,
    'list': return_list,
    'tuple': return_tuple,
    'response-none': return_response_none,
    'response-dict': return_response_dict,
    'response-list': return_response_list,
    'response-tuple': return_response_tuple,
    'html': return_html_response,
    'plain': return_plain_response,
    'template': return_template_response,
    'nothing-cls': ReturnNothing,
    'none-cls': ReturnNone,
    'dict-cls': ReturnDict,
    'str-cls': ReturnString,
    'list-cls': ReturnList,
    'tuple-cls': ReturnTuple,
    'basemodel': ReturnResponseBaseModel,
    'nested-basemodel': ReturnResponseNestedBaseModel,
    'model': ReturnResponseModel,
    'response-none-cls': ReturnResponseNone,
    'response-dict-cls': ReturnResponseDict,
    'response-list-cls': ReturnResponseList,
    'response-tuple-cls': ReturnResponseTuple,
    'html-cls': ReturnHTMLResponse,
    'template-cls': ReturnTemplateResponse,
    'plain-cls': ReturnPlainResponse,
    'stream': ReturnStreamingResponse,
    'async-stream': ReturnAsyncStreamingResponse,
    'full-cookies': full_cookie_api,
    'multiple-cookies': multiple_cookies_api,
    'default-cookies': default_cookies_api,
}


class TestResponses(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_nothing(self):
        res = await self.client.get('nothing/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_nothing_cls(self):
        res = await self.client.get('nothing-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_none(self):
        res = await self.client.get('none/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_none_cls(self):
        res = await self.client.get('none-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_dict(self):
        res = await self.client.get('dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '15'

    async def test_dict_cls(self):
        res = await self.client.get('dict-cls/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '15'

    async def test_string(self):
        res = await self.client.get('str/')
        assert res.status_code == 200
        assert res.data == 'Hello'
        assert res.body == b'"Hello"'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '7'

    async def test_string_cls(self):
        res = await self.client.get('str-cls/')
        assert res.status_code == 200
        assert res.data == 'Hello'
        assert res.body == b'"Hello"'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '7'

    async def test_list(self):
        res = await self.client.get('list/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3]
        assert res.body == b'[1,2,3]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '7'

    async def test_list_cls(self):
        res = await self.client.get('list-cls/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3]
        assert res.body == b'[1,2,3]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '7'

    async def test_tuple(self):
        res = await self.client.get('tuple/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3, 4]
        assert res.body == b'[1,2,3,4]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '9'

    async def test_tuple_cls(self):
        res = await self.client.get('tuple-cls/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3, 4]
        assert res.body == b'[1,2,3,4]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '9'

    async def test_basemodel(self):
        res = await self.client.get('basemodel/')
        assert res.status_code == 200
        assert res.data == {'name': 'John', 'age': 21, 'is_alive': True}
        assert res.body == b'{"name":"John","age":21,"is_alive":true}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '40'

    async def test_nested_basemodel(self):
        res = await self.client.get('nested-basemodel/')
        assert res.status_code == 200
        assert res.data == {
            'name': 'Ali',
            'book': {
                'title': 'Boo1',
                'author': {'name': 'John', 'age': 21, 'is_alive': True},
                'readers': [
                    {'name': 'Sara', 'age': 22, 'is_alive': True},
                    {'name': 'Sam', 'age': 5, 'is_alive': False},
                ],
            },
            'user': {'name': 'Ali', 'age': 2, 'is_alive': True},
            'books': [
                {'title': 'Book1', 'author': {'name': 'John1', 'age': 21, 'is_alive': True}, 'readers': []},
                {'title': 'Book2', 'author': {'name': 'John2', 'age': 22, 'is_alive': True}, 'readers': []},
            ],
        }
        assert res.body == (
            b'{"name":"Ali","book":{"title":"Boo1","author":{"name":"John","age":21,"is_alive":true},'
            b'"readers":[{"name":"Sara","age":22,"is_alive":true},{"name":"Sam","age":5,"is_alive":false}]},'
            b'"user":{"name":"Ali","age":2,"is_alive":true},'
            b'"books":[{"title":"Book1","author":{"name":"John1","age":21,"is_alive":true},"readers":[]},'
            b'{"title":"Book2","author":{"name":"John2","age":22,"is_alive":true},"readers":[]}]}'
        )
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '401'

    async def test_model(self):
        res = await self.client.get('model/')
        assert res.status_code == 200
        assert res.data == {'id': None, 'title': 'Fruit'}
        assert res.body == b'{"id":null,"title":"Fruit"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '27'

    async def test_response_none(self):
        res = await self.client.get('response-none/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_response_none_cls(self):
        res = await self.client.get('response-none-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '0'

    async def test_response_dict(self):
        res = await self.client.get('response-dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '15'

    async def test_response_dict_cls(self):
        res = await self.client.get('response-dict-cls/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '15'

    async def test_response_list(self):
        res = await self.client.get('response-list/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone']
        assert res.body == b'["car","home","phone"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '22'

    async def test_response_list_cls(self):
        res = await self.client.get('response-list-cls/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone']
        assert res.body == b'["car","home","phone"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '22'

    async def test_response_tuple(self):
        res = await self.client.get('response-tuple/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone', 'book']
        assert res.body == b'["car","home","phone","book"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '29'

    async def test_response_tuple_cls(self):
        res = await self.client.get('response-tuple-cls/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone', 'book']
        assert res.body == b'["car","home","phone","book"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Content-Length'] == '29'

    async def test_response_html(self):
        res = await self.client.get('html/')
        assert res.status_code == 200
        assert res.data == '<html><head><title></title></head></html>'
        assert res.body == b'<html><head><title></title></head></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Content-Length'] == '41'

    async def test_response_html_cls(self):
        res = await self.client.get('html-cls/')
        assert res.status_code == 200
        assert res.data == '<html><head><title></title></head></html>'
        assert res.body == b'<html><head><title></title></head></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Content-Length'] == '41'

    async def test_response_template(self) -> None:
        res: Response = await self.client.get('template/')
        assert res.status_code == 200
        assert res.data == '<html><body><p>Hello World</p></body></html>'
        assert res.body == b'<html><body><p>Hello World</p></body></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Content-Length'] == '44'

    async def test_response_template_cls(self) -> None:
        res: Response = await self.client.get('template-cls/')
        assert res.status_code == 200
        assert res.data == '<html><body><p>Hello World</p></body></html>'
        assert res.body == b'<html><body><p>Hello World</p></body></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Content-Length'] == '44'

    async def test_response_plain(self):
        res = await self.client.get('plain/')
        assert res.status_code == 200
        assert res.data == 'Hello World'
        assert res.body == b'Hello World'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert res.headers['Content-Length'] == '11'

    async def test_response_plain_cls(self):
        res = await self.client.get('plain-cls/')
        assert res.status_code == 200
        assert res.data == 'Hello World'
        assert res.body == b'Hello World'
        assert set(res.headers.keys()) == {'Content-Type', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert res.headers['Content-Length'] == '11'

    async def test_streaming_response(self):
        res = await self.client.get('stream/')
        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'application/octet-stream'
        assert res.data == '01234'
        assert res.body == b'01234'

    async def test_async_streaming_response(self):
        res = await self.client.get('async-stream/')
        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'application/octet-stream'
        assert res.data == '012345'
        assert res.body == b'012345'

    async def test_full_cookie(self):
        res = await self.client.get('full-cookies/')
        assert res.status_code == 200
        assert 'Set-Cookie' in res.headers
        assert res.headers['Set-Cookie'] == (
            'custom_key=custom_value; Domain=example.com; HttpOnly; Max-Age=100; Path=/here/; SameSite=strict; Secure'
        )
        assert res.cookies == [
            (
                b'Set-Cookie',
                b'custom_key=custom_value; '
                b'Domain=example.com; '
                b'HttpOnly; '
                b'Max-Age=100; '
                b'Path=/here/; '
                b'SameSite=strict; '
                b'Secure',
            )
        ]

    async def test_multiple_cookies(self):
        res = await self.client.get('multiple-cookies/')
        assert res.status_code == 200
        assert 'Set-Cookie' in res.headers
        assert res.cookies == [
            (
                b'Set-Cookie',
                b'custom_key1=custom_value1; Domain=example.com; HttpOnly; Max-Age=100; '
                b'Path=/here/; SameSite=strict; Secure',
            ),
            (
                b'Set-Cookie',
                b'custom_key2=custom_value2; Domain=example.com; HttpOnly; Max-Age=100; '
                b'Path=/here/; SameSite=strict; Secure',
            ),
        ]

    async def test_default_cookie(self):
        res = await self.client.get('default-cookies/')
        assert res.status_code == 200
        assert 'Set-Cookie' in res.headers
        assert res.cookies == [(b'Set-Cookie', b'custom_key=custom_value; Path=/; SameSite=lax')]
