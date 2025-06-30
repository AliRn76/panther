from pathlib import Path
from unittest import IsolatedAsyncioTestCase

import pytest

from panther import Panther
from panther.configs import config
from panther.db import Model
from panther.db.connections import db
from panther.generics import CreateAPI, DeleteAPI, ListAPI, RetrieveAPI, UpdateAPI
from panther.pagination import Pagination
from panther.request import Request
from panther.serializer import ModelSerializer
from panther.test import APIClient


class User(Model):
    name: str


class Person(User):
    age: int


class RetrieveAPITest(RetrieveAPI):
    async def get_instance(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


class ListAPITest(ListAPI):
    async def get_query(self, request: Request, **kwargs):
        return await User.find()


class FullListAPITest(ListAPI):
    sort_fields = ['name', 'age']
    search_fields = ['name']
    filter_fields = ['id', 'name', 'age']
    pagination = Pagination

    async def get_query(self, request: Request, **kwargs):
        return await Person.find()


class UserSerializer(ModelSerializer):
    class Config:
        model = User
        fields = '*'


class UpdateAPITest(UpdateAPI):
    input_model = UserSerializer

    async def get_instance(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


class CreateAPITest(CreateAPI):
    input_model = UserSerializer


class DeleteAPITest(DeleteAPI):
    async def get_instance(self, request: Request, **kwargs) -> Model:
        return await User.find_one(id=kwargs['id'])


urls = {
    'retrieve/<id>': RetrieveAPITest,
    'list': ListAPITest,
    'full-list': FullListAPITest,
    'update/<id>': UpdateAPITest,
    'create': CreateAPITest,
    'delete/<id>': DeleteAPITest,
}


class _BaseGenericTestCases:
    async def test_retrieve(self):
        user = await User.insert_one(name='Ali')
        res = await self.client.get(f'retrieve/{user.id}')
        assert res.status_code == 200
        assert res.data == {'id': str(user.id), 'name': user.name}

    async def test_list(self):
        users = await User.insert_many([{'name': 'Ali'}, {'name': 'Hamed'}])
        res = await self.client.get('list')
        assert res.status_code == 200
        assert res.data == [{'id': str(u.id), 'name': u.name} for u in users]

    async def test_list_features(self):
        users = await Person.insert_many(
            [
                {'name': 'Ali', 'age': 0},
                {'name': 'Ali', 'age': 1},
                {'name': 'Saba', 'age': 0},
                {'name': 'Saba', 'age': 1},
            ],
        )
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
        res = await self.client.get('full-list', query_params={'sort': 'name,-age', 'id': users[1].id})
        response = [{'id': r['id'], 'name': r['name'], 'age': r['age']} for r in res.data['results']]
        assert response == [{'id': str(users[1].id), 'name': 'Ali', 'age': 1}]

        # Filter 3
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

        new_users = list(await User.find())
        assert len(new_users)
        assert new_users[0].name == 'Sara'

    async def test_delete(self):
        users = await User.insert_many([{'name': 'Ali'}, {'name': 'Hamed'}])
        res = await self.client.delete(f'delete/{users[1].id}')
        assert res.status_code == 204
        new_users = list(await User.find())
        assert len(new_users) == 1
        assert new_users[0].model_dump() == users[0].model_dump()


class TestPantherDBGeneric(_BaseGenericTestCases, IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {'class': 'panther.db.connections.PantherDBConnection', 'path': cls.DB_PATH},
        }
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def tearDown(self) -> None:
        db.session.collection('User').drop()
        db.session.collection('Person').drop()

    @classmethod
    def tearDownClass(cls):
        config.refresh()
        Path(cls.DB_PATH).unlink(missing_ok=True)


@pytest.mark.mongodb
class TestMongoDBGeneric(_BaseGenericTestCases, IsolatedAsyncioTestCase):
    DB_NAME = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {
                'class': 'panther.db.connections.MongoDBConnection',
                'host': f'mongodb://127.0.0.1:27017/{cls.DB_NAME}',
            },
        }

    def setUp(self):
        app = Panther(__name__, configs=__name__, urls=urls)
        self.client = APIClient(app=app)

    def tearDown(self) -> None:
        db.session.drop_collection('User')
        db.session.drop_collection('Person')

    @classmethod
    def tearDownClass(cls):
        config.refresh()
