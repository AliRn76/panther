from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from panther import Panther
from panther.db import Model
from panther.generics import RetrieveAPI, ListAPI, UpdateAPI, DeleteAPI, CreateAPI
from panther.pagination import Pagination
from panther.request import Request
from panther.serializer import ModelSerializer
from panther.test import APIClient


class User(Model):
    name: str


class Person(User):
    age: int


class RetrieveAPITest(RetrieveAPI):
    async def object(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


class ListAPITest(ListAPI):
    async def cursor(self, request: Request, **kwargs):
        return await User.find()


class FullListAPITest(ListAPI):
    sort_fields = ['name', 'age']
    search_fields = ['name']
    filter_fields = ['name', 'age']
    pagination = Pagination

    async def cursor(self, request: Request, **kwargs):
        return await Person.find()


class UserSerializer(ModelSerializer):
    class Config:
        model = User
        fields = '*'


class UpdateAPITest(UpdateAPI):
    input_model = UserSerializer

    async def object(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


class CreateAPITest(CreateAPI):
    input_model = UserSerializer


class DeleteAPITest(DeleteAPI):
    async def object(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


urls = {
    'retrieve/<id>': RetrieveAPITest,
    'list': ListAPITest,
    'full-list': FullListAPITest,
    'update/<id>': UpdateAPITest,
    'create': CreateAPITest,
    'delete/<id>': DeleteAPITest,
}


class TestGeneric(IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.PantherDBConnection',
                'path': cls.DB_PATH
            },
        }
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def tearDown(self) -> None:
        Path(self.DB_PATH).unlink()

    async def test_retrieve(self):
        user = await User.insert_one(name='Ali')
        res = await self.client.get(f'retrieve/{user.id}')
        assert res.status_code == 200
        assert res.data == {'id': user.id, 'name': user.name}

    async def test_list(self):
        users = await User.insert_many([{'name': 'Ali'}, {'name': 'Hamed'}])
        res = await self.client.get('list')
        assert res.status_code == 200
        assert res.data == [{'id': u.id, 'name': u.name} for u in users]

    async def test_list_features(self):
        await Person.insert_many([
            {'name': 'Ali', 'age': 0},
            {'name': 'Ali', 'age': 1},
            {'name': 'Saba', 'age': 0},
            {'name': 'Saba', 'age': 1},
        ])
        res = await self.client.get('full-list')
        assert res.status_code == 200
        assert set(res.data.keys()) == {'results', 'count', 'previous', 'next'}

        # Normal
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Ali', 'age': 0},
            {'name': 'Ali', 'age': 1},
            {'name': 'Saba', 'age': 0},
            {'name': 'Saba', 'age': 1},
        ]

        # Sort 1
        res = await self.client.get('full-list', query_params={'sort': '-name'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Saba', 'age': 0},
            {'name': 'Saba', 'age': 1},
            {'name': 'Ali', 'age': 0},
            {'name': 'Ali', 'age': 1},
        ]

        # Sort 2
        res = await self.client.get('full-list', query_params={'sort': '-name,-age'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Saba', 'age': 1},
            {'name': 'Saba', 'age': 0},
            {'name': 'Ali', 'age': 1},
            {'name': 'Ali', 'age': 0},
        ]

        # Sort 3
        res = await self.client.get('full-list', query_params={'sort': 'name,-age'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Ali', 'age': 1},
            {'name': 'Ali', 'age': 0},
            {'name': 'Saba', 'age': 1},
            {'name': 'Saba', 'age': 0},
        ]

        # Filter 1
        res = await self.client.get('full-list', query_params={'sort': 'name,-age', 'name': 'Ali'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Ali', 'age': 1},
            {'name': 'Ali', 'age': 0},
        ]

        # Filter 2
        res = await self.client.get('full-list', query_params={'sort': 'name,-age', 'name': 'Alex'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == []

        # Search
        res = await self.client.get('full-list', query_params={'sort': 'name,-age', 'search': 'Ali'})
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Ali', 'age': 1},
            {'name': 'Ali', 'age': 0},
        ]

        # Pagination 1
        res = await self.client.get('full-list', query_params={'sort': 'name,-age'})
        assert res.data['previous'] is None
        assert res.data['next'] is None
        assert res.data['count'] == 4

        # Pagination 2
        res = await self.client.get('full-list', query_params={'limit': 2})
        assert res.data['previous'] is None
        assert res.data['next'] == '?limit=2&skip=2'
        assert res.data['count'] == 4
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Ali', 'age': 0},
            {'name': 'Ali', 'age': 1},
        ]

        res = await self.client.get('full-list', query_params={'limit': 2, 'skip': 2})
        assert res.data['previous'] == '?limit=2&skip=0'
        assert res.data['next'] is None
        assert res.data['count'] == 4
        response = [{'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [
            {'name': 'Saba', 'age': 0},
            {'name': 'Saba', 'age': 1},
        ]

    async def test_update(self):
        users = await User.insert_many([{'name': 'Ali'}, {'name': 'Hamed'}])
        res = await self.client.put(f'update/{users[1].id}', payload={'name': 'NewName'})
        assert res.status_code == 200
        assert res.data['name'] == 'NewName'

        new_users = await User.find()
        users[1].name = 'NewName'
        assert {(u.id, u.name) for u in new_users} == {(u.id, u.name) for u in users}

    async def test_create(self):
        res = await self.client.post('create', payload={'name': 'Sara'})
        assert res.status_code == 201
        assert res.data['name'] == 'Sara'

        new_users = await User.find()
        assert len([i for i in new_users])
        assert new_users[0].name == 'Sara'

    async def test_delete(self):
        users = await User.insert_many([{'name': 'Ali'}, {'name': 'Hamed'}])
        res = await self.client.delete(f'delete/{users[1].id}')
        assert res.status_code == 204
        new_users = await User.find()
        assert len([u for u in new_users]) == 1
        assert new_users[0].model_dump() == users[0].model_dump()
