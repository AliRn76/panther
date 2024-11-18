from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API, GenericAPI
from panther.response import Response, HTMLResponse, PlainTextResponse, StreamingResponse, TemplateResponse
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
            source='<html><body><p>{{ content }}</p></body></html>', context={'content': 'Hello World'}
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
            for i in range(5):
                yield i
        return StreamingResponse(f())


class ReturnAsyncStreamingResponse(GenericAPI):
    async def get(self):
        async def f():
            for i in range(6):
                yield i
        return StreamingResponse(f())


class ReturnInvalidStatusCode(GenericAPI):
    def get(self):
        return Response(status_code='ali')


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
    'response-none-cls': ReturnResponseNone,
    'response-dict-cls': ReturnResponseDict,
    'response-list-cls': ReturnResponseList,
    'response-tuple-cls': ReturnResponseTuple,
    'html-cls': ReturnHTMLResponse,
    'template-cls': ReturnTemplateResponse,
    'plain-cls': ReturnPlainResponse,
    'stream': ReturnStreamingResponse,
    'async-stream': ReturnAsyncStreamingResponse,
    'invalid-status-code': ReturnInvalidStatusCode,
}


class TestResponses(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    async def test_nothing(self):
        res = await self.client.get('nothing/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_nothing_cls(self):
        res = await self.client.get('nothing-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_none(self):
        res = await self.client.get('none/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_none_cls(self):
        res = await self.client.get('none-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_dict(self):
        res = await self.client.get('dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '15'

    async def test_dict_cls(self):
        res = await self.client.get('dict-cls/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '15'

    async def test_string(self):
        res = await self.client.get('str/')
        assert res.status_code == 200
        assert res.data == 'Hello'
        assert res.body == b'"Hello"'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '7'

    async def test_string_cls(self):
        res = await self.client.get('str-cls/')
        assert res.status_code == 200
        assert res.data == 'Hello'
        assert res.body == b'"Hello"'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '7'

    async def test_list(self):
        res = await self.client.get('list/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3]
        assert res.body == b'[1,2,3]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '7'

    async def test_list_cls(self):
        res = await self.client.get('list-cls/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3]
        assert res.body == b'[1,2,3]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '7'

    async def test_tuple(self):
        res = await self.client.get('tuple/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3, 4]
        assert res.body == b'[1,2,3,4]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '9'

    async def test_tuple_cls(self):
        res = await self.client.get('tuple-cls/')
        assert res.status_code == 200
        assert res.data == [1, 2, 3, 4]
        assert res.body == b'[1,2,3,4]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '9'

    async def test_response_none(self):
        res = await self.client.get('response-none/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_response_none_cls(self):
        res = await self.client.get('response-none-cls/')
        assert res.status_code == 200
        assert res.data is None
        assert res.body == b''
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '0'

    async def test_response_dict(self):
        res = await self.client.get('response-dict/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '15'

    async def test_response_dict_cls(self):
        res = await self.client.get('response-dict-cls/')
        assert res.status_code == 200
        assert res.data == {'detail': 'ok'}
        assert res.body == b'{"detail":"ok"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '15'

    async def test_response_list(self):
        res = await self.client.get('response-list/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone']
        assert res.body == b'["car","home","phone"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '22'

    async def test_response_list_cls(self):
        res = await self.client.get('response-list-cls/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone']
        assert res.body == b'["car","home","phone"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '22'

    async def test_response_tuple(self):
        res = await self.client.get('response-tuple/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone', 'book']
        assert res.body == b'["car","home","phone","book"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '29'

    async def test_response_tuple_cls(self):
        res = await self.client.get('response-tuple-cls/')
        assert res.status_code == 200
        assert res.data == ['car', 'home', 'phone', 'book']
        assert res.body == b'["car","home","phone","book"]'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '29'

    async def test_response_html(self):
        res = await self.client.get('html/')
        assert res.status_code == 200
        assert res.data == '<html><head><title></title></head></html>'
        assert res.body == b'<html><head><title></title></head></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '41'

    async def test_response_html_cls(self):
        res = await self.client.get('html-cls/')
        assert res.status_code == 200
        assert res.data == '<html><head><title></title></head></html>'
        assert res.body == b'<html><head><title></title></head></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '41'

    async def test_response_template(self) -> None:
        res: Response = await self.client.get('template/')
        assert res.status_code == 200
        assert res.data == '<html><body><p>Hello World</p></body></html>'
        assert res.body == b'<html><body><p>Hello World</p></body></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '44'

    async def test_response_template_cls(self) -> None:
        res: Response = await self.client.get('template-cls/')
        assert res.status_code == 200
        assert res.data == '<html><body><p>Hello World</p></body></html>'
        assert res.body == b'<html><body><p>Hello World</p></body></html>'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '44'

    async def test_response_plain(self):
        res = await self.client.get('plain/')
        assert res.status_code == 200
        assert res.data == 'Hello World'
        assert res.body == b'Hello World'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == '11'

    async def test_response_plain_cls(self):
        res = await self.client.get('plain-cls/')
        assert res.status_code == 200
        assert res.data == 'Hello World'
        assert res.body == b'Hello World'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
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

    async def test_invalid_status_code(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('invalid-status-code/')

        assert len(captured.records) == 1
        assert captured.records[0].getMessage().split('\n')[-2] == "TypeError: Response `status_code` Should Be `int`. (`ali` is <class 'str'>)"

        assert res.status_code == 500
        assert res.data == {'detail': 'Internal Server Error'}
        assert res.body == b'{"detail":"Internal Server Error"}'
        assert set(res.headers.keys()) == {'Content-Type', 'Access-Control-Allow-Origin', 'Content-Length'}
        assert res.headers['Content-Type'] == 'application/json'
        assert res.headers['Access-Control-Allow-Origin'] == '*'
        assert res.headers['Content-Length'] == 34
