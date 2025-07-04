from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API, GenericAPI
from panther.authentications import CookieJWTAuthentication, QueryParamJWTAuthentication
from panther.configs import config
from panther.db.models import BaseUser
from panther.request import Request
from panther.test import APIClient


class CustomAuth:
    async def __call__(self, request: Request):
        return 'THIS IS USER'


@API()
async def auth_required_api(request: Request):
    return request.user


@API()
async def refresh_token_api(request: Request):
    return await request.user.refresh_tokens()


@API()
async def logout_api(request: Request):
    return await request.user.logout()


@API(auth=CustomAuth)
async def custom_auth_api(request: Request):
    return request.user


async def custom_auth(req):
    return 'THIS IS USER'


@API(auth=custom_auth)
async def custom_auth_function_api(request: Request):
    return request.user


urls = {
    'auth-required': auth_required_api,
    'refresh-token': refresh_token_api,
    'logout': logout_api,
    'custom-auth': custom_auth_api,
    'custom-auth-function': custom_auth_function_api,
}


class User(BaseUser):
    username: str
    password: str


AUTHENTICATION = 'panther.authentications.JWTAuthentication'
SECRET_KEY = 'hvdhRspoTPh1cJVBHcuingQeOKNc1uRhIP2k7suLe2g='
DB_PATH = 'test.pdb'
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': DB_PATH,
    },
}
USER_MODEL = 'tests.test_authentication.User'


class TestJWTAuthentication(IsolatedAsyncioTestCase):
    SHORT_TOKEN = {'Authorization': 'Token TOKEN'}
    NOT_ENOUGH_SEGMENT_TOKEN = {'Authorization': 'Bearer XXX'}
    JUST_BEARER_TOKEN = {'Authorization': 'Bearer'}
    BAD_UNICODE_TOKEN = {'Authorization': 'Bearer علی'}
    BAD_SIGNATURE_TOKEN = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.JAWUkAU2mWhxcd6MS8r9pd44yBIfkEBmpr3WLeqIccM',
    }
    TOKEN_WITHOUT_USER_ID = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.PpyXW0PgmGSPaaNirm_Ei4Y2fw9nb4TN26RN1u9RHSo',
    }
    TOKEN = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.AF3nsj8IQ6t0ncqIx4quoyPfYaZ-pqUOW4z_euUztPM',
    }

    def setUp(self) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        self.client = APIClient(app=app)

    def tearDown(self) -> None:
        Path(DB_PATH).unlink()
        config.refresh()

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_user_auth_required_without_auth_class(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = None
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required')
        assert res.status_code == 200
        assert res.data is None
        config.AUTHENTICATION = auth_config

    async def test_user_auth_required_without_token(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required')

        assert res.status_code == 200
        assert res.data is None

    async def test_user_auth_required_with_bad_token_1(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.SHORT_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWTAuthentication Error: "Authorization keyword is not valid"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_bad_token2(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.JUST_BEARER_TOKEN)

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage() == 'JWTAuthentication Error: "Authorization header must contain 2 parts"'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_bad_token3(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.BAD_UNICODE_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == (
            "JWTAuthentication Error: \"'latin-1' codec can't encode characters in position 0-2: "
            'ordinal not in range(256)"'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_bad_token4(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.NOT_ENOUGH_SEGMENT_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWTAuthentication Error: "Not enough segments"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_invalid_token_signature(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.BAD_SIGNATURE_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWTAuthentication Error: "Signature verification failed."'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_token_without_user_id(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.TOKEN_WITHOUT_USER_ID)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWTAuthentication Error: "Payload does not have `user_id`"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_token_user_not_found(self):
        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', headers=self.TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWTAuthentication Error: "User not found"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_user_auth_required_with_token(self):
        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

        expected_response = {
            'id': user.id,
            'username': 'Username',
            'password': 'Password',
            'last_login': user.last_login.isoformat(),
            'date_created': user.date_created.isoformat(),
        }
        assert res.status_code == 200
        assert res.data == expected_response

    async def test_invalid_refresh_token(self):
        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('refresh-token', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage()
            == 'JWTAuthentication Error: "Invalid token type; expected `refresh` token."'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    async def test_refresh_token(self):
        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('refresh-token', headers={'Authorization': f'Bearer {tokens["refresh_token"]}'})

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'Redis is not connected; token revocation is not effective.'

        assert res.status_code == 200
        assert res.data.keys() == {'access_token', 'refresh_token'}

    async def test_cookie_authentication_without_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = CookieJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required', headers={'Authorization': f'Bearer {tokens["access_token"]}'})

        assert res.status_code == 200
        assert res.data is None

        config.AUTHENTICATION = auth_config

    async def test_cookie_authentication_invalid_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = CookieJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('auth-required', {'cookie': f'access_token=s'})

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'CookieJWTAuthentication Error: "Not enough segments"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

        config.AUTHENTICATION = auth_config

    async def test_cookie_authentication(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = CookieJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required', headers={'cookie': f'access_token={tokens["access_token"]}'})

        expected_response = {
            'id': user.id,
            'username': 'Username',
            'password': 'Password',
            'last_login': user.last_login.isoformat(),
            'date_created': user.date_created.isoformat(),
        }
        assert res.status_code == 200
        assert res.data == expected_response

        config.AUTHENTICATION = auth_config

    async def test_cookie_invalid_refresh_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = CookieJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('refresh-token', headers={'cookie': f'access_token={tokens["access_token"]}'})

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage()
            == 'CookieJWTAuthentication Error: "Invalid token type; expected `refresh` token."'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

        config.AUTHENTICATION = auth_config

    async def test_cookie_refresh_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = CookieJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get(
                'refresh-token',
                headers={'cookie': f'access_token={tokens["access_token"]}; refresh_token={tokens["refresh_token"]}'},
            )

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'Redis is not connected; token revocation is not effective.'
        assert res.status_code == 200
        assert res.data.keys() == {'access_token', 'refresh_token'}

        config.AUTHENTICATION = auth_config

    async def test_query_param_authentication_without_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = QueryParamJWTAuthentication

        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required')

        assert res.status_code == 200
        assert res.data is None

        config.AUTHENTICATION = auth_config

    async def test_query_param_authentication(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = QueryParamJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('auth-required', query_params={'authorization': tokens['access_token']})

        expected_response = {
            'id': user.id,
            'username': 'Username',
            'password': 'Password',
            'last_login': user.last_login.isoformat(),
            'date_created': user.date_created.isoformat(),
        }
        assert res.status_code == 200
        assert res.data == expected_response

        config.AUTHENTICATION = auth_config

    async def test_query_param_invalid_refresh_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = QueryParamJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('refresh-token', query_params={'authorization': tokens['access_token']})

        assert len(captured.records) == 1
        assert (
            captured.records[0].getMessage()
            == 'QueryParamJWTAuthentication Error: "Invalid token type; expected `refresh` token."'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

        config.AUTHENTICATION = auth_config

    async def test_query_param_refresh_token(self):
        auth_config = config.AUTHENTICATION
        config.AUTHENTICATION = QueryParamJWTAuthentication

        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('refresh-token', query_params={'authorization': tokens['refresh_token']})

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'Redis is not connected; token revocation is not effective.'
        assert res.status_code == 200
        assert res.data.keys() == {'access_token', 'refresh_token'}

        config.AUTHENTICATION = auth_config

    async def test_custom_auth_class(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('custom-auth')

        assert res.status_code == 200
        assert res.data == 'THIS IS USER'

    async def test_custom_auth_function(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('custom-auth-function')

        assert res.status_code == 200
        assert res.data == 'THIS IS USER'

    async def test_invalid_custom_auth_class(self):
        class SyncCustomAuth:
            def __call__(self, request: Request):
                return 'THIS IS USER'

        try:

            @API(auth=SyncCustomAuth)
            async def invalid_custom_auth_api(request: Request):
                return request.user
        except Exception as e:
            assert e.args[0] == 'SyncCustomAuth.__call__() should be `async`'
        else:
            assert False

    async def test_no_param_custom_auth_class(self):
        class InvalidCustomAuth:
            async def __call__(self):
                return 'THIS IS USER'

        try:

            @API(auth=InvalidCustomAuth)
            async def invalid_custom_auth_api(request: Request):
                return request.user
        except Exception as e:
            assert e.args[0] == 'InvalidCustomAuth.__call__() requires 2 positional argument(s) (self, request).'
        else:
            assert False

    async def test_invalid_custom_auth_function(self):
        def auth(req: str):
            pass

        try:

            @API(auth=auth)
            async def invalid_custom_auth_api(request: Request):
                return request.user
        except Exception as e:
            assert e.args[0] == 'auth() should be `async`'
        else:
            assert False

    async def test_no_param_custom_auth_function(self):
        def auth1():
            pass

        try:

            @API(auth=auth1)
            async def invalid_custom_auth_api(request: Request):
                return request.user
        except Exception as e:
            assert e.args[0] == 'auth1() requires 1 positional argument(s) (request).'
        else:
            assert False

    async def test_class_based_api_invalid_auth_type(self):
        def auth():
            pass

        try:

            class MyAPI(GenericAPI):
                auth = True
        except Exception as e:
            assert e.args[0] == (
                '`bool` is not valid for authentication, it should be a callable, a Class with __call__ '
                'method or a single function.'
            )
        else:
            assert False

    async def test_class_based_api_sync_function_auth(self):
        def auth_func(req):
            pass

        try:

            class MyAPI(GenericAPI):
                auth = auth_func
        except Exception as e:
            assert e.args[0] == 'auth_func() should be `async`'
        else:
            assert False

    async def test_class_based_api_no_param_function_auth(self):
        def auth_func2():
            pass

        try:

            class MyAPI(GenericAPI):
                auth = auth_func2
        except Exception as e:
            assert e.args[0] == 'auth_func2() requires 1 positional argument(s) (request).'
        else:
            assert False

    async def test_class_based_api_sync_class_auth(self):
        class CustomAuth1:
            def __call__(self, req):
                pass

        try:

            class MyAPI(GenericAPI):
                auth = CustomAuth1
        except Exception as e:
            assert e.args[0] == 'CustomAuth1.__call__() should be `async`'
        else:
            assert False

    async def test_class_based_api_no_param_class_auth(self):
        class CustomAuth2:
            def __call__(self):
                pass

        try:

            class MyAPI(GenericAPI):
                auth = CustomAuth2
        except Exception as e:
            assert e.args[0] == 'CustomAuth2.__call__() requires 2 positional argument(s) (self, request).'
        else:
            assert False

    async def test_class_based_api_class_without_call(self):
        class CustomAuth3:
            pass

        try:

            class MyAPI(GenericAPI):
                auth = CustomAuth3
        except Exception as e:
            assert e.args[0] == 'CustomAuth3 must implement __call__() method.'
        else:
            assert False

    async def test_class_based_api_class_with_initiated_auth(self):
        class CustomAuth4:
            pass

        try:

            class MyAPI(GenericAPI):
                auth = CustomAuth4()
        except Exception as e:
            assert (
                e.args[0]
                == '`CustomAuth4` is not valid for authentication, it should be a callable, a Class with __call__ method or a single function.'
            )
        else:
            assert False

    async def test_logout(self):
        user = await User.insert_one(username='Username', password='Password')
        tokens = await user.login()

        with self.assertLogs(level='ERROR') as captured:
            res = await self.client.get('logout', headers={'Authorization': f'Bearer {tokens["access_token"]}'})
        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'Redis is not connected; token revocation is not effective.'
        assert res.status_code == 200

        # TODO: We have to implement a mini redis to work with its functionalities even when its not connected.
        # with self.assertLogs(level='ERROR') as captured:
        #     res = await self.client.get('logout', headers={'Authorization': f'Bearer {tokens["access_token"]}'})
        # assert res.status_code == 401
