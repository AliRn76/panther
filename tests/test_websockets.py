from unittest import TestCase

import orjson as json

from panther import Panther, status
from panther.configs import config
from panther.test import WebsocketClient
from panther.websocket import GenericWebsocket


class WithoutAcceptWebsocket(GenericWebsocket):
    async def connect(self):
        pass


class CloseOnConnectWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.close()


class CustomCloseWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.close(code=status.WS_1013_TRY_AGAIN_LATER, reason='Come Back Later')


class MessageOnConnectWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.send('Hello')
        await self.close()


class QueryParamWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.send(self.query_params)
        await self.close()


class PathVariableWebsocket(GenericWebsocket):
    async def connect(self, name: str, age: int, is_male: bool):
        await self.accept()
        await self.send(
            f'{type(name).__name__}({name}), {type(age).__name__}({age}), {type(is_male).__name__}({is_male})'
        )
        await self.close()


class SendAllTypesWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()
        # Nothing
        await self.send()
        # None
        await self.send(None)
        # String
        await self.send('Hello Again')
        # Int
        await self.send(12)
        # Dict
        await self.send({'detail': 'ok'})
        # List
        await self.send([1, 2, 3, 'Ali', 4])
        # Tuple
        await self.send((1, 2, 3, 'Ali', 4))
        # Bytes
        await self.send(b'It Is Value Of A File')
        await self.close()


class WebsocketWithoutAuthentication(GenericWebsocket):
    async def connect(self):
        await self.accept()
        await self.send(str(self.user))
        await self.close()


class WebsocketWithAuthentication(GenericWebsocket):
    auth = True

    async def connect(self):
        await self.accept()
        await self.send(self.user)
        await self.close()


class Permission:
    @classmethod
    async def authorization(cls, connection) -> bool:
        if connection.path == '/with-permission':
            return True
        else:
            return False


class WebsocketWithPermission(GenericWebsocket):
    permissions = [Permission]

    async def connect(self):
        await self.accept()
        await self.send('ok')
        await self.close()


class WebsocketWithoutPermission(GenericWebsocket):
    permissions = [Permission]

    async def connect(self):
        await self.accept()
        await self.send('no')
        await self.close()


urls = {
    'without-accept': WithoutAcceptWebsocket,
    'close-on-connect': CloseOnConnectWebsocket,
    'custom-close': CustomCloseWebsocket,
    'message-after-connect': MessageOnConnectWebsocket,
    'query-params': QueryParamWebsocket,
    'path-variable/<name>/<age>/<is_male>/': PathVariableWebsocket,
    'all-types': SendAllTypesWebsocket,
    'without-auth': WebsocketWithoutAuthentication,
    'with-auth': WebsocketWithAuthentication,
    'with-permission': WebsocketWithPermission,
    'without-permission': WebsocketWithoutPermission,
}


class TestWebsocket(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config.HAS_WS = True
        cls.app = Panther(__name__, configs=__name__, urls=urls)

    def test_without_accept(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('without-accept')
        assert responses[0]['type'] == 'websocket.close'
        assert responses[0]['code'] == 1000
        assert responses[0]['reason'] == ''

    def test_close_on_connect(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('close-on-connect')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.close'
        assert responses[1]['code'] == 1000
        assert responses[1]['reason'] == ''

    def test_custom_close(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('custom-close')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.close'
        assert responses[1]['code'] == 1013
        assert responses[1]['reason'] == 'Come Back Later'

    def test_query_params(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('query-params', query_params={'name': 'ali', 'age': 27})
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        params = json.loads(responses[1]['text'])
        assert [*params.keys()] == ['name', 'age']
        assert params['name'] == 'ali'
        assert params['age'] == '27'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''

    def test_message_after_connect(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('message-after-connect')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == 'Hello'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''

    def test_path_variables(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('path-variable/Ali/25/true')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == 'str(Ali), int(25), bool(True)'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''

    def test_all_types(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('all-types')

        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        # String
        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == 'Hello Again'
        assert 'bytes' not in responses[1]
        # Int
        assert responses[2]['type'] == 'websocket.send'
        assert responses[2]['text'] == '12'
        assert 'bytes' not in responses[2]
        # Dict
        assert responses[3]['type'] == 'websocket.send'
        assert responses[3]['text'] == '{"detail":"ok"}'
        assert 'bytes' not in responses[3]
        # List
        assert responses[4]['type'] == 'websocket.send'
        assert responses[4]['text'] == '[1,2,3,"Ali",4]'
        assert 'bytes' not in responses[4]
        # Tuple
        assert responses[5]['type'] == 'websocket.send'
        assert responses[5]['text'] == '[1,2,3,"Ali",4]'
        assert 'bytes' not in responses[5]
        # Bytes
        assert responses[6]['type'] == 'websocket.send'
        assert responses[6]['bytes'] == b'It Is Value Of A File'
        assert 'text' not in responses[6]

        # Close
        assert responses[7]['type'] == 'websocket.close'
        assert responses[7]['code'] == 1000
        assert responses[7]['reason'] == ''

    def test_without_auth(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('without-auth')
        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == 'None'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''

    def test_with_auth_failed(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('with-auth')

        assert responses[0]['type'] == 'websocket.close'
        assert responses[0]['code'] == 1000
        assert responses[0]['reason'] == ''

    def test_with_auth_not_defined(self):
        ws = WebsocketClient(app=self.app)
        with self.assertLogs(level='ERROR') as captured:
            responses = ws.connect('with-auth?authorization=Bearer token')

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == '`WS_AUTHENTICATION` has not been set in configs'

        assert responses[0]['type'] == 'websocket.close'
        assert responses[0]['code'] == 1000
        assert responses[0]['reason'] == ''

    def test_with_auth_success(self):
        global WS_AUTHENTICATION, SECRET_KEY, DATABASE
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.PantherDBConnection',
            },
        }
        WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
        SECRET_KEY = 'hvdhRspoTPh1cJVBHcuingQeOKNc1uRhIP2k7suLe2g='
        token = 'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.AF3nsj8IQ6t0ncqIx4quoyPfYaZ-pqUOW4z_euUztPM'
        app = Panther(__name__, configs=__name__, urls=urls)
        WS_AUTHENTICATION = None
        SECRET_KEY = None
        DATABASE = None

        ws = WebsocketClient(app=app)
        with self.assertLogs(level='ERROR') as captured:
            responses = ws.connect('with-auth', query_params={'authorization': f'Bearer {token}'})

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "User not found"'

        assert responses[0]['type'] == 'websocket.close'
        assert responses[0]['code'] == 1000
        assert responses[0]['reason'] == ''

    def test_with_permission(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('with-permission')

        assert responses[0]['type'] == 'websocket.accept'
        assert responses[0]['subprotocol'] is None
        assert responses[0]['headers'] == {}

        assert responses[1]['type'] == 'websocket.send'
        assert responses[1]['text'] == 'ok'

        assert responses[2]['type'] == 'websocket.close'
        assert responses[2]['code'] == 1000
        assert responses[2]['reason'] == ''

    def test_without_permission(self):
        ws = WebsocketClient(app=self.app)
        responses = ws.connect('without-permission')

        assert responses[0]['type'] == 'websocket.close'
        assert responses[0]['code'] == 1000
        assert responses[0]['reason'] == ''
