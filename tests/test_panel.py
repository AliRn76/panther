from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.configs import config
from panther.db import Model
from panther.db.connections import db
from panther.db.models import BaseUser
from panther.panel.urls import url_routing
from panther.test import APIClient


class CustomUser(BaseUser):
    username: str
    password: str


class CustomModel(Model):
    name: str
    description: str = 'Default description'
    is_active: bool = True


# Test configuration
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
SECRET_KEY = 'hvdhRspoTPh1cJVBHcuingQeOKNc1uRhIP2k7suLe2g='
DB_PATH = 'test_panel.pdb'
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': DB_PATH,
    },
}
USER_MODEL = 'tests.test_panel.CustomUser'


class TestPanel(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = Panther(__name__, configs=__name__, urls={'': url_routing})
        cls.client = APIClient(app=app)

    def tearDown(self) -> None:
        db.session.collection('CustomUser').drop()
        db.session.collection('CustomModel').drop()

    @classmethod
    def tearDownClass(cls):
        config.refresh()
        Path(DB_PATH).unlink(missing_ok=True)

    @classmethod
    def check_in_cookies(cls, *args, cookies):
        cookies = {cookie[1] for cookie in cookies}
        for arg in args:
            for c in cookies:
                c.startswith(arg)
                break
            else:
                assert False

    async def test_login_view_get(self):
        """Test GET request to login page"""
        res = await self.client.get('login/')
        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_login_view_post_success(self):
        """Test successful login POST request"""
        # Create a test user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')

        # Test successful login
        res = await self.client.post(
            path='login/',
            payload={'username': 'testuser', 'password': 'testpass'},
        )
        self.check_in_cookies(b'access_token', b'refresh_token', cookies=res.cookies)
        assert res.status_code == 302  # Redirect

    async def test_login_view_post_user_not_found(self):
        """Test login POST request with non-existent user"""
        res = await self.client.post(
            path='login/',
            payload={'username': 'nonexistent', 'password': 'testpass'},
        )

        assert res.status_code == 400
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_login_view_post_wrong_password(self):
        """Test login POST request with wrong password"""
        # Create a test user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')

        # Test wrong password
        res = await self.client.post(
            path='login/',
            payload={'username': 'testuser', 'password': 'wrongpass'},
        )

        assert res.status_code == 400
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_login_view_post_with_redirect(self):
        """Test login POST request with redirect_to parameter"""
        # Create a test user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')

        # Test login with redirect
        res = await self.client.post(
            path='login/',
            payload={'username': 'testuser', 'password': 'testpass'},
            query_params={'redirect_to': '/admin/dashboard'},
        )

        assert res.status_code == 302
        self.check_in_cookies(b'access_token', b'refresh_token', cookies=res.cookies)

    async def test_home_view_without_auth(self):
        """Test home view without authentication"""
        res = await self.client.get('')
        assert res.status_code == 302  # Should redirect to login

    async def test_home_view_with_auth(self):
        """Test home view with authentication"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test home view with auth
        res = await self.client.get(path='', headers={'Cookie': f'access_token={tokens["access_token"]}'})

        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_table_view_without_auth(self):
        """Test table view without authentication"""
        res = await self.client.get('0/')
        assert res.status_code == 302  # Should redirect to login

    async def test_table_view_with_auth_empty_data(self):
        """Test table view with authentication but no data"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test table view with auth but no data
        res = await self.client.get(path='0/', headers={'Cookie': f'access_token={tokens["access_token"]}'})

        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_table_view_with_auth_with_data(self):
        """Test table view with authentication and data"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Create some test data
        await CustomModel.insert_one(name='Test Item 1', description='Description 1')
        await CustomModel.insert_one(name='Test Item 2', description='Description 2')

        # Test table view with auth and data
        res = await self.client.get(
            path='1/',  # CustomModel should be at index 1 (after CustomUser at index 0)
            headers={'Cookie': f'access_token={tokens["access_token"]}'},
        )

        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_create_view_get_without_auth(self):
        """Test create view GET without authentication"""
        res = await self.client.get('0/create/')
        assert res.status_code == 302  # Should redirect to login

    async def test_create_view_get_with_auth(self):
        """Test create view GET with authentication"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test create view GET with auth
        res = await self.client.get(path='0/create/', headers={'Cookie': f'access_token={tokens["access_token"]}'})

        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_create_view_post_without_auth(self):
        """Test create view POST without authentication"""
        res = await self.client.post('0/create/', payload={'username': 'newuser', 'password': 'newpass'})
        assert res.status_code == 302  # Should redirect to login

    async def test_create_view_post_with_auth_user_model(self):
        """Test create view POST with authentication for user model"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test create user with auth
        res = await self.client.post(
            path='0/create/',
            payload={'username': 'newuser', 'password': 'newpass'},
            headers={'Cookie': f'access_token={tokens["access_token"]}'},
        )

        assert res.status_code == 200
        assert res.data['username'] == 'newuser'
        # Password should be hashed
        assert res.data['password'] != 'newpass'

    async def test_create_view_post_with_auth_regular_model(self):
        """Test create view POST with authentication for regular model"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test create regular model with auth
        res = await self.client.post(
            path='1/create/',
            payload={'name': 'New Item', 'description': 'New Description', 'is_active': True},
            headers={'Cookie': f'access_token={tokens["access_token"]}'},
        )

        assert res.status_code == 200
        assert res.data['name'] == 'New Item'
        assert res.data['description'] == 'New Description'
        assert res.data['is_active'] is True

    async def test_detail_view_get_without_auth(self):
        """Test detail view GET without authentication"""
        res = await self.client.get('0/test-id/')
        assert res.status_code == 302  # Should redirect to login

    async def test_detail_view_get_with_auth(self):
        """Test detail view GET with authentication"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Create a test item
        test_item = await CustomModel.insert_one(name='Test Item', description='Test Description')

        # Test detail view GET with auth
        res = await self.client.get(
            path=f'1/{test_item.id}/', headers={'Cookie': f'access_token={tokens["access_token"]}'}
        )

        assert res.status_code == 200
        assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    async def test_detail_view_put_without_auth(self):
        """Test detail view PUT without authentication"""
        res = await self.client.put('0/test-id/', payload={'username': 'updated'})
        assert res.status_code == 302  # Should redirect to login

    async def test_detail_view_put_with_auth(self):
        """Test detail view PUT with authentication"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Create a test item
        test_item = await CustomModel.insert_one(name='Test Item', description='Test Description')

        # Test detail view PUT with auth
        res = await self.client.put(
            path=f'1/{test_item.id}/',
            payload={'name': 'Updated Item', 'description': 'Updated Description'},
            headers={'Cookie': f'access_token={tokens["access_token"]}'},
        )

        assert res.status_code == 200
        assert res.data['name'] == 'Updated Item'
        assert res.data['description'] == 'Updated Description'

    async def test_detail_view_delete_without_auth(self):
        """Test detail view DELETE without authentication"""
        res = await self.client.delete('0/test-id/')
        assert res.status_code == 302  # Should redirect to login

    async def test_detail_view_delete_with_auth(self):
        """Test detail view DELETE with authentication"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Create a test item
        test_item = await CustomModel.insert_one(name='Test Item', description='Test Description')

        # Test detail view DELETE with auth
        res = await self.client.delete(
            path=f'1/{test_item.id}/', headers={'Cookie': f'access_token={tokens["access_token"]}'}
        )

        assert res.status_code == 204  # No content

        # Verify item was deleted
        deleted_item = await CustomModel.find_one(id=test_item.id)
        assert deleted_item is None

    async def test_invalid_model_index(self):
        """Test accessing invalid model index"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test invalid model index
        res = await self.client.get(path='999/', headers={'Cookie': f'access_token={tokens["access_token"]}'})

        assert res.status_code == 500  # Should raise an error for invalid index

    async def test_invalid_document_id(self):
        """Test accessing invalid document ID"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test invalid document ID
        res = await self.client.get(path='0/invalid-id/', headers={'Cookie': f'access_token={tokens["access_token"]}'})

        assert res.status_code == 404  # Should raise an error for invalid document ID

    async def test_middleware_redirect_to_slash(self):
        """Test RedirectToSlashMiddleware functionality"""
        # Create and login user
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')
        tokens = await user.login()

        # Test without trailing slash (should redirect)
        res = await self.client.get(path='login', headers={'Cookie': f'access_token={tokens["access_token"]}'})
        assert res.status_code == 307  # Redirect to add trailing slash

    async def test_cookie_authentication_invalid_token(self):
        """Test cookie authentication with invalid token"""
        res = await self.client.get(path='', headers={'Cookie': 'access_token=invalid_token'})

        assert res.status_code == 302  # Should redirect to login

    async def test_cookie_authentication_expired_token(self):
        """Test cookie authentication with expired token"""
        # Create a user but don't use their token
        user = await CustomUser.insert_one(username='testuser', password='testpass')
        await user.set_password('testpass')

        # Use an expired token
        expired_token = (
            'eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJpYXQiOjE2MzQ1Njc4NzQsImV4cCI6MTYzNDU2Nzg3NX0.invalid_signature'
        )

        res = await self.client.get(path='', headers={'Cookie': f'access_token={expired_token}'})

        assert res.status_code == 302  # Should redirect to login
