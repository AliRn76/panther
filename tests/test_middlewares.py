from unittest import IsolatedAsyncioTestCase, TestCase

from panther import Panther
from panther.app import API
from panther.base_websocket import Websocket
from panther.configs import config
from panther.middlewares.base import HTTPMiddleware, WebsocketMiddleware
from panther.request import Request
from panther.test import APIClient, WebsocketClient
from panther.websocket import GenericWebsocket


class MyMiddleware(HTTPMiddleware):
    async def __call__(self, request: Request):
        request.middlewares = [*getattr(request, 'middlewares', []), 'MyMiddleware']
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'MyMiddleware']
        return response


class BeforeMiddleware1(HTTPMiddleware):
    async def __call__(self, request: Request):
        request.middlewares = [*getattr(request, 'middlewares', []), 'BeforeMiddleware1']
        return await self.dispatch(request=request)


class BeforeMiddleware2(HTTPMiddleware):
    async def __call__(self, request: Request):
        request.middlewares = [*getattr(request, 'middlewares', []), 'BeforeMiddleware2']
        return await self.dispatch(request=request)


class AfterMiddleware1(HTTPMiddleware):
    async def __call__(self, request: Request):
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'AfterMiddleware1']
        return response


class AfterMiddleware2(HTTPMiddleware):
    async def __call__(self, request: Request):
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'AfterMiddleware2']
        return response


class AfterMiddleware3(HTTPMiddleware):
    async def __call__(self, request: Request):
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'AfterMiddleware3']
        return response


class MyWSMiddleware1(WebsocketMiddleware):
    async def __call__(self, connection: Websocket):
        connection.middlewares = [*getattr(connection, 'middlewares', []), 'MyWSMiddleware1']
        return await self.dispatch(connection=connection)


class MyWSMiddleware2(WebsocketMiddleware):
    async def __call__(self, connection: Websocket):
        connection.middlewares = [*getattr(connection, 'middlewares', []), 'MyWSMiddleware2']
        return await self.dispatch(connection=connection)


class PrivateMiddleware1(HTTPMiddleware):
    async def __call__(self, request: Request):
        request.middlewares = [*getattr(request, 'middlewares', []), 'PrivateMiddleware1']
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'PrivateMiddleware1']
        return response


class PrivateMiddleware2(HTTPMiddleware):
    async def __call__(self, request: Request):
        request.middlewares = [*getattr(request, 'middlewares', []), 'PrivateMiddleware2']
        response = await self.dispatch(request=request)
        response.data = [*response.data, 'PrivateMiddleware2']
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
    def tearDown(self):
        config.refresh()

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
        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                MIDDLEWARES = []

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage()
            == "Invalid 'MIDDLEWARES': <class 'tests.test_middlewares.MyWSMiddleware1'> is not a sub class of `HTTPMiddleware`"
        )

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
            'PrivateMiddleware1',
        ]

    async def test_middlewares_order(self):
        global MIDDLEWARES
        MIDDLEWARES = [
            BeforeMiddleware2,
            AfterMiddleware3,
            MyMiddleware,
            BeforeMiddleware1,
            AfterMiddleware1,
            AfterMiddleware2,
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
            'MyMiddleware',
            'PrivateMiddleware1',
            'PrivateMiddleware2',
            'FunctionCall',
            'PrivateMiddleware2',
            'PrivateMiddleware1',
            'MyMiddleware',
            'AfterMiddleware2',
            'AfterMiddleware1',
            'MyMiddleware',
            'AfterMiddleware3',
        ]
        MIDDLEWARES = []


class TestWebsocketMiddleware(TestCase):
    @classmethod
    def tearDownClass(cls):
        config.refresh()

    def setUp(self):
        config.HAS_WS = True

    def tearDown(self):
        config.refresh()

    def test_websocket_middleware(self):
        global WS_MIDDLEWARES
        WS_MIDDLEWARES = [MyWSMiddleware1, MyWSMiddleware2]
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
        WS_MIDDLEWARES = []

    def test_http_middleware_in_websocket(self):
        global WS_MIDDLEWARES
        WS_MIDDLEWARES = [MyWSMiddleware1, MyMiddleware, MyWSMiddleware2]
        with self.assertLogs(level='ERROR') as captured:
            try:
                Panther(name=__name__, configs=__name__, urls={})
            except SystemExit:
                assert True
            else:
                assert False
            finally:
                WS_MIDDLEWARES = []

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage()
            == "Invalid 'WS_MIDDLEWARES': <class 'tests.test_middlewares.MyMiddleware'> is not a sub class of `WebsocketMiddleware`"
        )

    def test_base_middleware(self):
        global WS_MIDDLEWARES
        WS_MIDDLEWARES = [MyWSMiddleware1, MyWSMiddleware2]
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
        WS_MIDDLEWARES = []
