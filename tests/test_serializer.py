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


class NotRequiredFieldsSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ['author', 'pages_count']


class RequiredFieldsSerializer(ModelSerializer):
    class Meta:
        model = Book
        fields = ['name', 'author', 'pages_count']


class OnlyRequiredFieldsSerializer(ModelSerializer):
    class Meta:
        model = Book
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

    def test_define_class_without_meta(self):
        try:
            class Serializer0(ModelSerializer):
                pass
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`class Meta` is required in tests.test_serializer.Serializer0.'
        else:
            assert False

    def test_define_class_without_model(self):
        try:
            class Serializer1(ModelSerializer):
                class Meta:
                    pass
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer1.Meta.model` is required.'
        else:
            assert False

    def test_define_class_without_fields(self):
        try:
            class Serializer2(ModelSerializer):
                class Meta:
                    model = Book
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer2.Meta.fields` is required.'
        else:
            assert False

    def test_define_class_with_invalid_fields(self):
        try:
            class Serializer3(ModelSerializer):
                class Meta:
                    model = Book
                    fields = ['ok', 'no']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer3.Meta.fields.ok` is not valid.'
        else:
            assert False

    def test_define_class_with_invalid_required_fields(self):
        try:
            class Serializer4(ModelSerializer):
                class Meta:
                    model = Book
                    fields = ['name', 'author']
                    required_fields = ['pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer4.Meta.required_fields.pages_count` should be in `Meta.fields` too.'
        else:
            assert False

    def test_define_class_with_invalid_model(self):
        try:
            class Serializer5(ModelSerializer):
                class Meta:
                    model = ModelSerializer
                    fields = ['name', 'author', 'pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer5.Meta.model` is not subclass of `panther.db.Model`.'
        else:
            assert False
