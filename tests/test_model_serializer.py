from pathlib import Path
from unittest import TestCase

from pydantic import Field

from panther import Panther
from panther.app import API
from panther.db import Model
from panther.request import Request
from panther.serializer import ModelSerializer
from panther.test import APIClient


class Book(Model):
    name: str
    author: str = Field('default_author')
    pages_count: int = Field(0)


class NotRequiredFieldsSerializer(metaclass=ModelSerializer, model=Book):
    fields = ['author', 'pages_count']


class RequiredFieldsSerializer(metaclass=ModelSerializer, model=Book):
    fields = ['name', 'author', 'pages_count']


class OnlyRequiredFieldsSerializer(metaclass=ModelSerializer, model=Book):
    fields = ['name', 'author', 'pages_count']
    required_fields = ['author', 'pages_count']


@API(input_model=NotRequiredFieldsSerializer)
async def not_required(request: Request):
    return request.validated_data


@API(input_model=RequiredFieldsSerializer)
async def required(request: Request):
    return request.validated_data


@API(input_model=OnlyRequiredFieldsSerializer)
async def only_required(request: Request):
    return request.validated_data


urls = {
    'not-required': not_required,
    'required': required,
    'only-required': only_required,
}


class TestModelSerializer(TestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global MIDDLEWARES
        MIDDLEWARES = [
            ('panther.middlewares.db.DatabaseMiddleware', {'url': f'pantherdb://{cls.DB_PATH}'}),
        ]
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def tearDown(self) -> None:
        Path(self.DB_PATH).unlink(missing_ok=True)

    def test_not_required_fields_empty_response(self):
        payload = {}
        res = self.client.post('not-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'author': 'default_author', 'pages_count': 0}

    def test_not_required_fields_full_response(self):
        payload = {
            'author': 'ali',
            'pages_count': '12'
        }
        res = self.client.post('not-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'author': 'ali', 'pages_count': 12}

    def test_required_fields_error(self):
        payload = {}
        res = self.client.post('required', payload=payload)
        assert res.status_code == 400
        assert res.data == {'name': 'Field required'}

    def test_required_fields_success(self):
        payload = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = self.client.post('required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12}

    def test_only_required_fields_error(self):
        payload = {}
        res = self.client.post('only-required', payload=payload)
        assert res.status_code == 400
        assert res.data == {'name': 'Field required', 'author': 'Field required', 'pages_count': 'Field required'}

    def test_only_required_fields_success(self):
        payload = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = self.client.post('only-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12}

    def test_define_class_without_fields(self):
        try:
            class Serializer1(metaclass=ModelSerializer, model=Book):
                pass
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == "'fields' required while using 'ModelSerializer' metaclass. -> tests.test_model_serializer.Serializer1"
        else:
            assert False

    def test_define_class_with_invalid_fields(self):
        try:
            class Serializer2(metaclass=ModelSerializer, model=Book):
                fields = ['ok', 'no']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == "'ok' is not in 'Book' -> tests.test_model_serializer.Serializer2"
        else:
            assert False

    def test_define_class_with_invalid_required_fields(self):
        try:
            class Serializer3(metaclass=ModelSerializer, model=Book):
                fields = ['name', 'author']
                required_fields = ['pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == "'pages_count' is in 'required_fields' but not in 'fields' -> tests.test_model_serializer.Serializer3"
        else:
            assert False

    def test_define_class_without_model(self):
        try:
            class Serializer4(metaclass=ModelSerializer):
                fields = ['name', 'author']
                required_fields = ['pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == "'model' required while using 'ModelSerializer' metaclass -> tests.test_model_serializer.Serializer4"
        else:
            assert False

    def test_define_class_without_metaclass(self):
        class Serializer5(ModelSerializer):
            fields = ['name', 'author']
            required_fields = ['pages_count']

        try:
            Serializer5(name='alice', author='bob')
        except Exception as e:
            assert isinstance(e, TypeError)
            assert e.args[0] == "you should not inherit the 'ModelSerializer', you should use it as 'metaclass' -> tests.test_model_serializer.Serializer5"
        else:
            assert False
