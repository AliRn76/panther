import asyncio
from pathlib import Path
from unittest import TestCase

from panther import Panther
from panther.app import API
from panther.configs import config
from panther.db import Model
from panther.request import Request
from panther.test import APIClient


@API()
async def without_auth(request: Request):
    return request.user


@API(auth=True)
async def auth_required(request: Request):
    return request.user


urls = {
    'without': without_auth,
    'auth-required': auth_required,
}


class User(Model):
    username: str
    password: str


AUTHENTICATION = 'panther.authentications.JWTAuthentication'
SECRET_KEY = 'hvdhRspoTPh1cJVBHcuingQeOKNc1uRhIP2k7suLe2g='
DB_PATH = 'test.pdb'
MIDDLEWARES = [
    ('panther.middlewares.db.DatabaseMiddleware', {'url': f'pantherdb://{DB_PATH}'}),
]
USER_MODEL = 'tests.test_authentication.User'


class TestAuthentication(TestCase):
    SHORT_TOKEN = {'Authorization': 'TOKEN'}
    NOT_ENOUGH_SEGMENT_TOKEN = {'Authorization': 'Bearer XXX'}
    JUST_BEARER_TOKEN = {'Authorization': 'Bearer'}
    BAD_UNICODE_TOKEN = {'Authorization': 'Bearer علی'}
    BAD_SIGNATURE_TOKEN = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.JAWUkAU2mWhxcd6MS8r9pd44yBIfkEBmpr3WLeqIccM'}
    TOKEN_WITHOUT_USER_ID = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.PpyXW0PgmGSPaaNirm_Ei4Y2fw9nb4TN26RN1u9RHSo'}
    TOKEN = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.AF3nsj8IQ6t0ncqIx4quoyPfYaZ-pqUOW4z_euUztPM'}

    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def setUp(self) -> None:
        for middleware in config['http_middlewares']:
            asyncio.run(middleware.before(request=None))

    def tearDown(self) -> None:
        for middleware in config['reversed_http_middlewares']:
            asyncio.run(middleware.after(response=None))
        Path(DB_PATH).unlink()

    def test_user_without_auth(self):
        res = self.client.get('without')
        assert res.status_code == 200
        assert res.data is None

        res = self.client.get('without', headers={'Authorization': 'Token'})
        assert res.status_code == 200
        assert res.data is None

    def test_user_auth_required_without_auth_class(self):
        auth_config = config['authentication']
        config['authentication'] = None
        with self.assertLogs(level='CRITICAL') as captured:
            res = self.client.get('auth-required')
        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == '"AUTHENTICATION" has not been set in configs'
        assert res.status_code == 500
        assert res.data['detail'] == 'Internal Server Error'
        config['authentication'] = auth_config

    def test_user_auth_required_without_token(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required')

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Authorization is required"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_bad_token_1(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.SHORT_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Authorization keyword is not valid"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_bad_token2(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.JUST_BEARER_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Authorization should have 2 part"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_bad_token3(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.BAD_UNICODE_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == (
            'JWT Authentication Error: "\'latin-1\' codec can\'t encode characters in position 7-9: '
            'ordinal not in range(256)"'
        )
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_bad_token4(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.NOT_ENOUGH_SEGMENT_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Not enough segments"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_invalid_token_signature(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.BAD_SIGNATURE_TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Signature verification failed."'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_token_without_user_id(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.TOKEN_WITHOUT_USER_ID)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "Payload does not have user_id"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_token_user_not_found(self):
        with self.assertLogs(level='ERROR') as captured:
            res = self.client.get('auth-required', headers=self.TOKEN)

        assert len(captured.records) == 1
        assert captured.records[0].getMessage() == 'JWT Authentication Error: "User not found"'
        assert res.status_code == 401
        assert res.data['detail'] == 'Authentication Error'

    def test_user_auth_required_with_token(self):
        User.insert_one(username='Username', password='Password')

        with self.assertNoLogs(level='ERROR'):
            res = self.client.get('auth-required', headers=self.TOKEN)

        assert res.status_code == 200
        assert [*res.data.keys()] == ['id', 'username', 'password']
        assert res.data['id'] == '1'
        assert res.data['username'] == 'Username'
        assert res.data['password'] == 'Password'
