from pathlib import Path
from typing import ClassVar
from unittest import IsolatedAsyncioTestCase

from pydantic import BaseModel, Field

from panther import Panther
from panther.configs import config
from panther.db import Model
from panther.db.connections import db
from panther.db.models import ID
from panther.response import Response


class OutputModelWithAlias(BaseModel):
    id: ID | None = Field(None, validation_alias='_id', alias='_id')
    name: str


class OutputModelWithPrepare(BaseModel):
    value: int

    async def to_response(self, instance, data):
        # Just return the data with a custom key for test
        return {'custom': data['value']}


class User(Model):
    username: str
    password: str


class UserOutputSerializer(BaseModel):
    id: str
    username: str


class OutputModelWithInstanceCheck(BaseModel):
    value: int
    called_with: ClassVar = []  # class variable to record calls

    async def to_response(self, instance, data):
        # Record the arguments for assertion
        OutputModelWithInstanceCheck.called_with.append((instance, data))
        return {'value': data['value'], 'instance_type': type(instance).__name__}


class OutputModelWithInstanceCheckIterable(BaseModel):
    value: int
    called_with: ClassVar = []

    async def to_response(self, instance, data):
        OutputModelWithInstanceCheckIterable.called_with.append((instance, data))
        return {'value': data['value'], 'instance_type': type(instance).__name__}


class TestResponsesOutputModel(IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASE
        DATABASE = {
            'engine': {'class': 'panther.db.connections.PantherDBConnection', 'path': cls.DB_PATH},
        }
        Panther(__name__, configs=__name__, urls={})

    def tearDown(self) -> None:
        db.session.collection('Book').drop()

    @classmethod
    def tearDownClass(cls):
        config.refresh()
        Path(cls.DB_PATH).unlink(missing_ok=True)

    async def test_dict(self):
        resp = Response(data={'_id': 1, 'name': 'foo'})
        await resp.serialize_output(OutputModelWithAlias)
        assert resp.data == {'id': '1', 'name': 'foo'}

    async def test_iterable(self):
        resp = Response(data=[{'_id': 1, 'name': 'foo'}, {'_id': 2, 'name': 'bar'}])
        await resp.serialize_output(OutputModelWithAlias)
        assert resp.data == [{'id': '1', 'name': 'foo'}, {'id': '2', 'name': 'bar'}]

    async def test_to_response(self):
        resp = Response(data={'value': 42})
        await resp.serialize_output(OutputModelWithPrepare)
        assert resp.data == {'custom': 42}

    async def test_iterable_to_response(self):
        resp = Response(data=[{'value': 1}, {'value': 2}])
        await resp.serialize_output(OutputModelWithPrepare)
        assert resp.data == [{'custom': 1}, {'custom': 2}]

    async def test_type_error(self):
        resp = Response(data='not a dict')
        with self.assertRaises(TypeError):
            await resp.serialize_output(OutputModelWithAlias)

    async def test_model(self):
        user = await User.insert_one(username='Ali', password='1234')
        resp = Response(data=user)
        await resp.serialize_output(UserOutputSerializer)
        assert resp.data == {'id': user.id, 'username': 'Ali'}

    async def test_to_response_instance_argument(self):
        OutputModelWithInstanceCheck.called_with.clear()
        resp = Response(data={'value': 123, 'etc': 'ok'})
        await resp.serialize_output(OutputModelWithInstanceCheck)
        # The instance should be the original data dict
        assert resp.data == {'value': 123, 'instance_type': 'dict'}
        assert OutputModelWithInstanceCheck.called_with[0][0] == {'value': 123, 'etc': 'ok'}
        assert OutputModelWithInstanceCheck.called_with[0][1] == {'value': 123}

    async def test_iterable_to_response_instance_argument(self):
        OutputModelWithInstanceCheckIterable.called_with.clear()
        data = [{'value': 1, 'etc': 'ok'}, {'value': 2, 'etc': 'ok'}]
        resp = Response(data=data)
        await resp.serialize_output(OutputModelWithInstanceCheckIterable)
        # The instance should be the original list for each call
        assert resp.data == [
            {'value': 1, 'instance_type': 'dict'},
            {'value': 2, 'instance_type': 'dict'},
        ]
        # Both calls should have the same instance (the dict)
        assert OutputModelWithInstanceCheckIterable.called_with[0][0] == {'value': 1, 'etc': 'ok'}
        assert OutputModelWithInstanceCheckIterable.called_with[1][0] == {'value': 2, 'etc': 'ok'}
        assert OutputModelWithInstanceCheckIterable.called_with[0][1] == {'value': 1}
        assert OutputModelWithInstanceCheckIterable.called_with[1][1] == {'value': 2}

    async def test_model_instance_to_response_argument(self):
        class UserOutputWithInstance(BaseModel):
            id: str
            username: str
            called_with: ClassVar = []

            async def to_response(self, instance, data):
                UserOutputWithInstance.called_with.append((instance, data))
                return {'id': data['id'], 'username': data['username'], 'instance_type': type(instance).__name__}

        UserOutputWithInstance.called_with.clear()
        user = await User.insert_one(username='Ali', password='1234')
        resp = Response(data=user)
        await resp.serialize_output(UserOutputWithInstance)
        assert resp.data['id'] == user.id
        assert resp.data['username'] == 'Ali'
        assert resp.data['instance_type'] == 'User'
        assert UserOutputWithInstance.called_with[0][0] is user
        assert UserOutputWithInstance.called_with[0][1]['id'] == user.id
