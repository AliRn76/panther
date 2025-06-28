from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API, GenericAPI
from panther.configs import config
from panther.exceptions import PantherError
from panther.permissions import BasePermission
from panther.request import Request
from panther.test import APIClient


class AlwaysDeniedPermission(BasePermission):
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return False


class NotInheritedPermission:
    @classmethod
    async def authorization(cls, request: Request) -> bool:
        return False


class NotClassMethodPermission(BasePermission):
    async def authorization(cls, request: Request) -> bool:
        return False


class SyncPermission(BasePermission):
    @classmethod
    def authorization(cls, request: Request) -> bool:
        return False


@API()
async def without_permission_api(request: Request):
    return request.user


@API(permissions=[AlwaysDeniedPermission])
async def denied_permission_api(request: Request):
    return request.user


@API(permissions=[NotInheritedPermission])
async def not_inherited_permission_api(request: Request):
    return request.user


urls = {
    'without': without_permission_api,
    'denied-permission': denied_permission_api,
    'not-inherited-permission': not_inherited_permission_api,
}


class TestJWTAuthentication(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        app = Panther(__name__, configs=__name__, urls=urls)
        self.client = APIClient(app=app)

    @classmethod
    def tearDownClass(cls):
        config.refresh()

    async def test_without_permission(self):
        res = await self.client.get('without')
        assert res.status_code == 200
        assert res.data is None

    async def test_denied_permission(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('denied-permission')
        assert res.status_code == 403
        assert res.data['detail'] == 'Permission Denied'

    async def test_not_inherited_permission(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('not-inherited-permission')
        assert res.status_code == 403
        assert res.data['detail'] == 'Permission Denied'

    async def test_not_classmethod_permission(self):
        try:

            @API(permissions=[NotClassMethodPermission])
            async def not_classmethod_permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'NotClassMethodPermission.authorization() should be `@classmethod`'
        else:
            assert False

    async def test_not_classmethod_permission_classbased(self):
        try:

            class NotClassMethodPermissionAPI(GenericAPI):
                permissions = [NotClassMethodPermission]
        except PantherError as e:
            assert e.args[0] == 'NotClassMethodPermission.authorization() should be `@classmethod`'
        else:
            assert False

    async def test_sync_permission(self):
        try:

            @API(permissions=[SyncPermission])
            async def sync_permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'SyncPermission.authorization() should be `async`'
        else:
            assert False

    async def test_sync_permission_classbased(self):
        try:

            class SyncPermissionAPI(GenericAPI):
                permissions = [SyncPermission]
        except PantherError as e:
            assert e.args[0] == 'SyncPermission.authorization() should be `async`'
        else:
            assert False
