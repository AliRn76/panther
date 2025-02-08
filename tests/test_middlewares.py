from unittest import IsolatedAsyncioTestCase, TestCase

from panther import Panther
from panther.app import API
from panther.configs import config
from panther.middlewares import BaseMiddleware
from panther.middlewares.base import HTTPMiddleware, WebsocketMiddleware
from panther.request import Request
from panther.response import Response
from panther.test import APIClient, WebsocketClient
from panther.websocket import GenericWebsocket


class EmptyBaseMiddleware(BaseMiddleware):
    pass


class MyMiddleware(HTTPMiddleware):
    async def before(self, request: Request):
        request.middlewares = getattr(request, 'middlewares', []) + ['MyMiddleware']
        return request

    async def after(self, response: Response):
        response.data = response.data + ['MyMiddleware']
        return response


class BeforeMiddleware1(HTTPMiddleware):
    async def before(self, request: Request):
        request.middlewares = getattr(request, 'middlewares', []) + ['BeforeMiddleware1']
        return request


class BeforeMiddleware2(HTTPMiddleware):
    async def before(self, request: Request):
        request.middlewares = getattr(request, 'middlewares', []) + ['BeforeMiddleware2']
        return request


class AfterMiddleware1(HTTPMiddleware):
    async def after(self, response: Response):
        response.data = response.data + ['AfterMiddleware1']
        return response


class AfterMiddleware2(HTTPMiddleware):
    async def after(self, response: Response):
        response.data = response.data + ['AfterMiddleware2']
        return response


class AfterMiddleware3(HTTPMiddleware):
    async def after(self, response: Response):
        response.data = response.data + ['AfterMiddleware3']
        return response


class MyWSMiddleware1(WebsocketMiddleware):
    async def before(self, request: GenericWebsocket):
        request.middlewares = getattr(request, 'middlewares', []) + ['MyWSMiddleware1']
        return request

    async def after(self, response: GenericWebsocket):
        return response


class MyWSMiddleware2(WebsocketMiddleware):
    async def before(self, request: GenericWebsocket):
        request.middlewares = getattr(request, 'middlewares', []) + ['MyWSMiddleware2']
        return request

    async def after(self, response: GenericWebsocket):
        return response


class MyBaseMiddleware(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket):
        request.middlewares = getattr(request, 'middlewares', []) + ['MyBaseMiddleware']
        return request

    async def after(self, response: Response | GenericWebsocket):
        if isinstance(response, Response):
            response.data = response.data + ['MyBaseMiddleware']
        return response


class PrivateMiddleware1(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket):
        request.middlewares = getattr(request, 'middlewares', []) + ['PrivateMiddleware1']
        return request

    async def after(self, response: Response):
        response.data = response.data + ['PrivateMiddleware1']
        return response


class PrivateMiddleware2(BaseMiddleware):
    async def before(self, request: Request | GenericWebsocket):
        request.middlewares = getattr(request, 'middlewares', []) + ['PrivateMiddleware2']
        return request

    async def after(self, response: Response):
        response.data = response.data + ['PrivateMiddleware2']
        return response


@API()
async def handle_middlewares(request: Request):
    states = ['FunctionCall']
    if hasattr(request, 'middlewares'):
        states = request.middlewares + states
    return states


@API(middlewares=[])
async def handle_private_empty_middlewares(request: Request):
    states = ['FunctionCall']
    if hasattr(request, 'middlewares'):
        states = request.middlewares + states
    return states


@API(middlewares=[PrivateMiddleware1, PrivateMiddleware2])
async def handle_private_middlewares(request: Request):
    states = ['FunctionCall']
    if hasattr(request, 'middlewares'):
        states = request.middlewares + states
    return states


class WebsocketHandleMiddlewares(GenericWebsocket):
    async def connect(self):
        await self.accept()
        states = ['WebsocketConnect']
        if hasattr(self, 'middlewares'):
            states = self.middlewares + states
        await self.send(states)
        await self.close()


urls = {
    '': handle_middlewares,
    'private-empty': handle_private_empty_middlewares,
    'private': handle_private_middlewares,
    'websocket': WebsocketHandleMiddlewares,
}


class TestMiddleware(IsolatedAsyncioTestCase):
    async def test_empty_base_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [EmptyBaseMiddleware]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)

        response = await client.get('')
        assert response.status_code == 200
        assert response.data == ['FunctionCall']
        MIDDLEWARES = []

    async def test_before_base_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [BeforeMiddleware1]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('')
        assert response.status_code == 200
        assert response.data == ['BeforeMiddleware1', 'FunctionCall']
        MIDDLEWARES = []

    async def test_after_base_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [AfterMiddleware1]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('')
        assert response.status_code == 200
        assert response.data == ['FunctionCall', 'AfterMiddleware1']
        MIDDLEWARES = []

    async def test_a_normal_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [MyMiddleware]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('')
        assert response.status_code == 200
        assert response.data == ['MyMiddleware', 'FunctionCall', 'MyMiddleware']

    async def test_websocket_middleware_in_http(self):
        global MIDDLEWARES
        MIDDLEWARES = [MyWSMiddleware1]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('')
        assert response.status_code == 200
        assert response.data == ['FunctionCall']
        MIDDLEWARES = []

    async def test_private_empty_middleware(self):
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('private-empty')
        assert response.status_code == 200
        assert response.data == ['FunctionCall']

    async def test_private_middleware(self):
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('private')
        assert response.status_code == 200
        assert response.data == [
            'PrivateMiddleware1',
            'PrivateMiddleware2',
            'FunctionCall',
            'PrivateMiddleware2',
            'PrivateMiddleware1'
        ]

    async def test_middlewares_order(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            BeforeMiddleware2,
            AfterMiddleware3,
            MyMiddleware,
            BeforeMiddleware1,
            MyWSMiddleware1,
            AfterMiddleware1,
            AfterMiddleware2,
            MyBaseMiddleware,
            MyMiddleware,
        ]
        app = Panther(__name__, configs=__name__, urls=urls)
        client = APIClient(app=app)
        response = await client.get('private')
        assert response.status_code == 200
        assert response.data == [
            'BeforeMiddleware2',
            'MyMiddleware',
            'BeforeMiddleware1',
            'MyBaseMiddleware',
            'MyMiddleware',
            'PrivateMiddleware1',
            'PrivateMiddleware2',
            'FunctionCall',
            'PrivateMiddleware2',
            'PrivateMiddleware1',
            'MyMiddleware',
            'MyBaseMiddleware',
            'AfterMiddleware2',
            'AfterMiddleware1',
            'MyMiddleware',
            'AfterMiddleware3',
        ]
        MIDDLEWARES = []


class TestWebsocketMiddleware(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config.HAS_WS = True  # Required for `pytest` (`unittest` is fine)

    def test_websocket_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [MyWSMiddleware1, MyWSMiddleware2]
        app = Panther(__name__, configs=__name__, urls=urls)
        ws = WebsocketClient(app=app)
        responses = ws.connect('websocket')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == '["MyWSMiddleware1","MyWSMiddleware2","WebsocketConnect"]'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''
        MIDDLEWARES = []

    def test_http_middleware_in_websocket(self):
        global MIDDLEWARES
        MIDDLEWARES = [MyWSMiddleware1, MyMiddleware, MyWSMiddleware2]
        app = Panther(__name__, configs=__name__, urls=urls)
        ws = WebsocketClient(app=app)
        responses = ws.connect('websocket')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == '["MyWSMiddleware1","MyWSMiddleware2","WebsocketConnect"]'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''
        MIDDLEWARES = []

    def test_base_middleware(self):
        global MIDDLEWARES
        MIDDLEWARES = [MyWSMiddleware1, MyBaseMiddleware, MyWSMiddleware2]
        app = Panther(__name__, configs=__name__, urls=urls)
        ws = WebsocketClient(app=app)
        responses = ws.connect('websocket')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == '["MyWSMiddleware1","MyBaseMiddleware","MyWSMiddleware2","WebsocketConnect"]'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''
        MIDDLEWARES = []
