from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.app import API, GenericAPI
from panther.configs import config
from panther.exceptions import PantherError
from panther.permissions import BasePermission
from panther.request import Request
from panther.test import APIClient


class AlwaysDeniedPermission(BasePermission):
    async def __call__(self, request: Request) -> bool:
        return False


class NotInheritedPermission:
    async def __call__(self, request: Request) -> bool:
        return False


class SyncPermission(BasePermission):
    def __call__(self, request: Request) -> bool:
        return False


class WithoutParamPermission:
    def __call__(self) -> bool:
        return False


def without_param_permission():
    return False


class WithoutCallPermission:
    pass


def sync_permission(req):
    return False


async def accept_permission(req):
    return True


async def deny_permission(req):
    return True


@API()
async def without_permission_api(request: Request):
    return request.user


@API(permissions=[AlwaysDeniedPermission])
async def denied_permission_api(request: Request):
    return request.user


@API(permissions=AlwaysDeniedPermission)
async def single_denied_permission_api(request: Request):
    return request.user


@API(permissions=[NotInheritedPermission])
async def not_inherited_permission_api(request: Request):
    return request.user


@API(permissions=[accept_permission, accept_permission, AlwaysDeniedPermission])
async def multiple_permissions_api(request: Request):
    return request.user


urls = {
    'without': without_permission_api,
    'denied-permission': denied_permission_api,
    'single-denied-permission': single_denied_permission_api,
    'not-inherited-permission': not_inherited_permission_api,
    'multiple-permission': multiple_permissions_api,
}


class TestPermission(IsolatedAsyncioTestCase):
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

    async def test_single_denied_permission(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('single-denied-permission')
        assert res.status_code == 403
        assert res.data['detail'] == 'Permission Denied'

    async def test_not_inherited_permission(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('not-inherited-permission')
        assert res.status_code == 403
        assert res.data['detail'] == 'Permission Denied'

    async def test_multiple_permission(self):
        with self.assertNoLogs(level='ERROR'):
            res = await self.client.get('multiple-permission')
        assert res.status_code == 403
        assert res.data['detail'] == 'Permission Denied'

    async def test_sync_permission(self):
        try:

            @API(permissions=[SyncPermission])
            async def sync_permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'SyncPermission.__call__() should be `async`'
        else:
            assert False

    async def test_sync_permission_classbased(self):
        try:

            class SyncPermissionAPI(GenericAPI):
                permissions = [SyncPermission]
        except PantherError as e:
            assert e.args[0] == 'SyncPermission.__call__() should be `async`'
        else:
            assert False

    async def test_without_call_permission(self):
        try:

            @API(permissions=[WithoutCallPermission])
            async def permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'WithoutCallPermission must implement __call__() method.'
        else:
            assert False

    async def test_without_call_permission_classbased(self):
        try:

            class PermissionAPI(GenericAPI):
                permissions = [WithoutCallPermission]
        except PantherError as e:
            assert e.args[0] == 'WithoutCallPermission must implement __call__() method.'
        else:
            assert False

    async def test_sync_function_permission(self):
        try:

            @API(permissions=[sync_permission])
            async def permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'sync_permission() should be `async`'
        else:
            assert False

    async def test_sync_function_permission_classbased(self):
        try:

            class PermissionAPI(GenericAPI):
                permissions = [sync_permission]
        except PantherError as e:
            assert e.args[0] == 'sync_permission() should be `async`'
        else:
            assert False

    async def test_class_without_param_permission(self):
        try:

            @API(permissions=[WithoutParamPermission])
            async def permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'WithoutParamPermission.__call__() requires 2 positional argument(s) (self, request).'
        else:
            assert False

    async def test_class_without_param_permission_classbased(self):
        try:

            class PermissionAPI(GenericAPI):
                permissions = [WithoutParamPermission]
        except PantherError as e:
            assert e.args[0] == 'WithoutParamPermission.__call__() requires 2 positional argument(s) (self, request).'
        else:
            assert False

    async def test_function_without_param_permission(self):
        try:

            @API(permissions=[without_param_permission])
            async def permission_api(request: Request):
                return request.user
        except PantherError as e:
            assert e.args[0] == 'without_param_permission() requires 1 positional argument(s) (request).'
        else:
            assert False

    async def test_function_without_param_permission_classbased(self):
        try:

            class PermissionAPI(GenericAPI):
                permissions = [without_param_permission]
        except PantherError as e:
            assert e.args[0] == 'without_param_permission() requires 1 positional argument(s) (request).'
        else:
            assert False
