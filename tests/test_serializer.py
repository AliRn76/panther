from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from pydantic import Field, ConfigDict
from pydantic import field_validator

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
    class Config:
        model = Book
        fields = ['author', 'pages_count']


class RequiredFieldsSerializer(ModelSerializer):
    class Config:
        model = Book
        fields = ['name', 'author', 'pages_count']


class OnlyRequiredFieldsSerializer(ModelSerializer):
    class Config:
        model = Book
        fields = ['name', 'author', 'pages_count']
        required_fields = ['author', 'pages_count']


class WithValidatorsSerializer(ModelSerializer):
    class Config:
        model = Book
        fields = ['name', 'author', 'pages_count']
        required_fields = ['author', 'pages_count']

    @field_validator('name', 'author', 'pages_count')
    def validate_other(cls, field):
        return 'validated'

    @field_validator('pages_count')
    def validate_pages_count(cls, field):
        return 100


class WithClassFieldsSerializer(ModelSerializer):
    age: int = Field(10)

    class Config:
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


@API(input_model=WithValidatorsSerializer)
async def with_validators(request: Request):
    return request.validated_data


@API(input_model=WithClassFieldsSerializer)
async def with_class_fields(request: Request):
    return request.validated_data


urls = {
    'not-required': not_required,
    'required': required,
    'only-required': only_required,
    'with-validators': with_validators,
    'class-fields': with_class_fields,
}


class TestModelSerializer(IsolatedAsyncioTestCase):
    DB_PATH = 'test.pdb'

    @classmethod
    def setUpClass(cls) -> None:
        global DATABASES
        DATABASES = {
            'engine': 'panther.db.connections.PantherDBConnection'
        }
        app = Panther(__name__, configs=__name__, urls=urls)
        cls.client = APIClient(app=app)

    def tearDown(self) -> None:
        Path(self.DB_PATH).unlink(missing_ok=True)

    # # # Class Usage

    async def test_not_required_fields_empty_response(self):
        payload = {}
        res = await self.client.post('not-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'author': 'default_author', 'pages_count': 0}

    async def test_not_required_fields_full_response(self):
        payload = {
            'author': 'ali',
            'pages_count': '12'
        }
        res = await self.client.post('not-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'author': 'ali', 'pages_count': 12}

    async def test_required_fields_error(self):
        payload = {}
        res = await self.client.post('required', payload=payload)
        assert res.status_code == 400
        assert res.data == {'name': 'Field required'}

    async def test_required_fields_success(self):
        payload = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = await self.client.post('required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12}

    async def test_only_required_fields_error(self):
        payload = {}
        res = await self.client.post('only-required', payload=payload)
        assert res.status_code == 400
        assert res.data == {'name': 'Field required', 'author': 'Field required', 'pages_count': 'Field required'}

    async def test_only_required_fields_success(self):
        payload = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = await self.client.post('only-required', payload=payload)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12}

    async def test_with_validators(self):
        payload = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = await self.client.post('with-validators', payload=payload)
        assert res.status_code == 200
        assert res.data == {'name': 'validated', 'author': 'validated', 'pages_count': 100}

    async def test_with_class_fields_success(self):
        # Test Default Value
        payload1 = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12'
        }
        res = await self.client.post('class-fields', payload=payload1)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12, 'age': 10}

        # Test Validation
        payload2 = {
            'name': 'how to code',
            'author': 'ali',
            'pages_count': '12',
            'age': 30
        }
        res = await self.client.post('class-fields', payload=payload2)
        assert res.status_code == 200
        assert res.data == {'name': 'how to code', 'author': 'ali', 'pages_count': 12, 'age': 30}

    # # # Class Definition

    async def test_define_class_without_meta(self):
        try:
            class Serializer0(ModelSerializer):
                pass
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`class Config` is required in tests.test_serializer.Serializer0.'
        else:
            assert False

    async def test_define_class_without_model(self):
        try:
            class Serializer1(ModelSerializer):
                class Config:
                    pass
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer1.Config.model` is required.'
        else:
            assert False

    async def test_define_class_without_fields(self):
        try:
            class Serializer2(ModelSerializer):
                class Config:
                    model = Book
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer2.Config.fields` is required.'
        else:
            assert False

    async def test_define_class_with_invalid_fields(self):
        try:
            class Serializer3(ModelSerializer):
                class Config:
                    model = Book
                    fields = ['ok', 'no']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer3.Config.fields.ok` is not in `Book.model_fields`'
        else:
            assert False

    async def test_define_class_with_invalid_required_fields(self):
        try:
            class Serializer4(ModelSerializer):
                class Config:
                    model = Book
                    fields = ['name', 'author']
                    required_fields = ['pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer4.Config.required_fields.pages_count` should be in `Config.fields` too.'
        else:
            assert False

    async def test_define_class_with_invalid_model(self):
        try:
            class Serializer5(ModelSerializer):
                class Config:
                    model = ModelSerializer
                    fields = ['name', 'author', 'pages_count']
        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer5.Config.model` is not subclass of `panther.db.Model`.'
        else:
            assert False

    async def test_define_class_with_invalid_exclude_1(self):
        try:
            class Serializer6(ModelSerializer):
                class Config:
                    model = Book
                    fields = ['name', 'author', 'pages_count']
                    exclude = ['not_found']

        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer6.Config.exclude.not_found` is not valid.'
        else:
            assert False

    async def test_define_class_with_invalid_exclude_2(self):
        try:
            class Serializer7(ModelSerializer):
                class Config:
                    model = Book
                    fields = ['name', 'pages_count']
                    exclude = ['author']

        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == '`Serializer7.Config.exclude.author` is not defined in `Config.fields`.'
        else:
            assert False

    async def test_with_star_fields_with_exclude3(self):
        try:
            class Serializer8(ModelSerializer):
                class Config:
                    model = Book
                    fields = ['*']
                    exclude = ['author']

        except Exception as e:
            assert isinstance(e, AttributeError)
            assert e.args[0] == "`Serializer8.Config.fields.*` is not valid. Did you mean `fields = '*'`"
        else:
            assert False

    # # # Serializer Usage
    async def test_with_simple_model_config(self):
        class Serializer(ModelSerializer):
            model_config = ConfigDict(str_to_upper=True)

            class Config:
                model = Book
                fields = ['name', 'author', 'pages_count']

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert serialized.name == 'BOOK'
        assert serialized.author == 'ALIRN'
        assert serialized.pages_count == 12

    async def test_with_inner_model_config(self):
        class Serializer(ModelSerializer):
            class Config:
                str_to_upper = True
                model = Book
                fields = ['name', 'author', 'pages_count']

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert serialized.name == 'BOOK'
        assert serialized.author == 'ALIRN'
        assert serialized.pages_count == 12

    async def test_with_dual_model_config(self):
        class Serializer(ModelSerializer):
            model_config = ConfigDict(str_to_upper=False)

            class Config:
                str_to_upper = True
                model = Book
                fields = ['name', 'author', 'pages_count']

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert serialized.name == 'book'
        assert serialized.author == 'AliRn'
        assert serialized.pages_count == 12

    async def test_serializer_doc(self):
        class Serializer1(ModelSerializer):
            """Hello I'm Doc"""
            class Config:
                model = Book
                fields = ['name', 'author', 'pages_count']

        serialized = Serializer1(name='book', author='AliRn', pages_count='12')
        assert serialized.__doc__ == 'Hello I\'m Doc'

        class Serializer2(ModelSerializer):
            class Config:
                model = Book
                fields = ['name', 'author', 'pages_count']

        serialized = Serializer2(name='book', author='AliRn', pages_count='12')
        assert serialized.__doc__ is None

    async def test_with_exclude(self):
        class Serializer(ModelSerializer):
            class Config:
                model = Book
                fields = ['name', 'author', 'pages_count']
                exclude = ['author']

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert set(serialized.model_dump().keys()) == {'name', 'pages_count'}
        assert serialized.name == 'book'
        assert serialized.pages_count == 12

    async def test_with_star_fields(self):
        class Serializer(ModelSerializer):
            class Config:
                model = Book
                fields = '*'

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert set(serialized.model_dump().keys()) == {'id', 'name', 'author', 'pages_count'}
        assert serialized.name == 'book'
        assert serialized.author == 'AliRn'
        assert serialized.pages_count == 12

    async def test_with_star_fields_with_exclude(self):
        class Serializer(ModelSerializer):
            class Config:
                model = Book
                fields = '*'
                exclude = ['author']

        serialized = Serializer(name='book', author='AliRn', pages_count='12')
        assert set(serialized.model_dump().keys()) == {'id', 'name', 'pages_count'}
        assert serialized.name == 'book'
        assert serialized.pages_count == 12
