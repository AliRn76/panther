from pathlib import Path
from unittest import IsolatedAsyncioTestCase

import pytest
from pydantic import BaseModel, Field

from panther import Panther
from panther.app import API, GenericAPI
from panther.configs import config
from panther.db import Model
from panther.db.connections import db
from panther.db.models import ID
from panther.response import Cookie, HTMLResponse, PlainTextResponse, Response, StreamingResponse, TemplateResponse
from panther.test import APIClient


class OutputModelWithAlias(BaseModel):
    id: ID | None = Field(None, validation_alias='_id', alias='_id')
    name: str


class OutputModelWithPrepare(BaseModel):
    value: int

    async def prepare_response(self, instance, data):
        # Just return the data with a custom key for test
        return {'custom': data['value']}


class User(Model):
    username: str
    password: str


class UserOutputSerializer(BaseModel):
    id: str
    username: str


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
        result = await resp.apply_output_model(OutputModelWithAlias)
        assert result == {'id': '1', 'name': 'foo'}

    async def test_iterable(self):
        resp = Response(data=[{'_id': 1, 'name': 'foo'}, {'_id': 2, 'name': 'bar'}])
        result = await resp.apply_output_model(OutputModelWithAlias)
        assert result == [{'id': '1', 'name': 'foo'}, {'id': '2', 'name': 'bar'}]

    async def test_prepare_response(self):
        resp = Response(data={'value': 42})
        result = await resp.apply_output_model(OutputModelWithPrepare)
        assert result == {'custom': 42}

    async def test_iterable_prepare_response(self):
        resp = Response(data=[{'value': 1}, {'value': 2}])
        result = await resp.apply_output_model(OutputModelWithPrepare)
        assert result == [{'custom': 1}, {'custom': 2}]

    async def test_type_error(self):
        resp = Response(data='not a dict')
        with self.assertRaises(TypeError):
            await resp.apply_output_model(OutputModelWithAlias)

    async def test_model(self):
        user = await User.insert_one(username='Ali', password='1234')
        resp = Response(data=user)
        result = await resp.apply_output_model(UserOutputSerializer)
        assert result == {'id': user.id, 'username': 'Ali'}
