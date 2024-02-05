import typing
from collections.abc import MutableMapping

import bson
from pydantic import BaseModel, create_model, field_validator
from pydantic.fields import FieldInfo, Field


class Document(MutableMapping):
    def __new__(cls, *args, **kwargs):
        print(f'New {cls=}, {args}, {kwargs}')
        cls._required_fields = {k for k, v in cls.model_fields.items() if v.is_required and k != 'metadata_'}
        return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        print(f'\nInitialized -> {args}, {kwargs}, {self.__class__}\n')
        self.cls = self.__class__
        self.metadata_ = {'__class__': self.__class__}
        # breakpoint()

    def __getitem__(self, key):
        if key == '_id':
            key = 'id'
        print(f'{id(self)=} {self._required_fields=}= Get -> {key=}')
        if hasattr(self, key):
            getattr(self, key)
        else:
            return self.metadata_[key]

    def __setitem__(self, key, value):
        if key == '_id':
            key = 'id'
        #     value = str(value)
        print(f'{id(self)=} + Set -> {key=}, {value=}')
        # if hasattr(self, key):
        #     setattr(self, key, value)
        # else:
        self.metadata_[key] = value

        print(set(self.metadata_.keys()), self._required_fields, self._required_fields == set(self.metadata_.keys()))
        if set(self.metadata_.keys()) == self._required_fields:
            # breakpoint()
            obj = self.__class__(**self.metadata_)
            print(f'{obj=}\n')

    def __copy__(self):
        print(f'{id(self)=} Copy -> {id(self)}')

    def __call__(self, *args, **kwargs):
        return self

    def __del__(self):
        print(f'{id(self)=} Del --> {self=}')

    def __delitem__(self, key):
        print(f'DelItem -> {key=}')
        del self.metadata_[key]

    def __iter__(self):
        print(f'Iter -> ')
        return iter(self.metadata_)

    def __len__(self):
        print(f'Len -> ')
        return len(self.metadata_)


class MetaModel:
    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[typing.Any], ...],
            namespace: dict[str, typing.Any],
            **kwargs
    ):
        print(f'{cls_name=}')
        if cls_name == 'Model':
            return super().__new__(cls)

        field_definitions = {
            key: (value, namespace.get(key, FieldInfo(annotation=value)))
            for key, value in namespace.pop('__annotations__', {}).items()
        }

        return create_model(
            __model_name=cls_name,
            __module__=namespace['__module__'],
            __validators__=namespace,
            __base__=(BaseModel, Document),
            **field_definitions
        )


class Model(metaclass=MetaModel):
    pass


class User(Model):
    metadata_: dict = Field({}, exclude=True, )
    id: str | None = Field(None)
    # _id: str | None = PrivateAttr()
    name: str

    # def __new__(cls, *args, **kwargs):
    #     print(f'User.__new__')
    #     return super().__new__(cls)
    #
    # def __init__(self):
    #     print(f'User.__init__')
    #     return super().__init__(self.__class__)


    @field_validator('id', mode='before')
    def validate_id(cls, value: str | int | bson.ObjectId) -> str:
        if isinstance(value, int):
            pass

        elif isinstance(value, str):
            try:
                bson.ObjectId(value)
            except bson.objectid.InvalidId as e:
                msg = 'Invalid ObjectId'
                raise ValueError(msg) from e

        elif not isinstance(value, bson.ObjectId):
            msg = 'ObjectId required'
            raise ValueError(msg) from None

        return str(value)


from bson.codec_options import CodecOptions

# document_class = Document(User)
codec = CodecOptions(document_class=User)

from pymongo import MongoClient

db = MongoClient()
# db = MongoClient(document_class=dict).get_database('Test')

deleted_count = db.get_database('Test', codec_options=codec).session['User'].delete_many({})
print(f'{deleted_count=}')
inserted = db.get_database('Test', codec_options=codec).session['User'].insert_one({'name': 'Ali'})
print(f'{inserted=}')
users = db.get_database('Test', codec_options=codec).session['User'].find()
# for u in users:
#     print(f'{u=}')
print(f'{users[0]=}')
# print('ok')
# print(f'{users[1].model_dump()=}')
