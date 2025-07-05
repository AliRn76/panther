from collections import defaultdict
from types import NoneType
from typing import Any

from pydantic import BaseModel

from panther.configs import config
from panther.response import IterableDataTypes


def _ref_name(ref: str) -> str:
    obj_name = ref.rsplit('/', maxsplit=1)[1]
    return f'${obj_name}'


def clean_model_schema(schema: dict) -> dict:
    """
    Example:
        {
        'title': 'Author',
        '$': {
            'Book': {
                'title': 'Book',
                'fields': {
                    'title': {'title': 'Title', 'type': ['string'], 'required': True},
                    'pages_count': {'title': 'Pages Count', 'type': ['integer'], 'required': True},
                    'readers': {'title': 'Readers', 'type': ['array', 'null'], 'items': '$Person', 'default': None, 'required': False},
                    'co_owner': {'type': ['$Person', 'null'], 'default': None, 'required': False}
                }
            },
            'Parent': {
                'title': 'Parent',
                'fields': {
                    'name': {'title': 'Name', 'type': ['string'], 'required': True},
                    'age': {'title': 'Age', 'type': ['string'], 'required': True},
                    'has_child': {'title': 'Has Child', 'type': ['boolean'], 'required': True}
                }
            },
            'Person': {
                'title': 'Person',
                'fields': {
                    'age': {'title': 'Age', 'type': ['integer'], 'required': True},
                    'real_name': {'title': 'Real Name', 'type': ['string'], 'required': True},
                    'parent': {'type': '$Parent', 'required': True},
                    'is_alive': {'title': 'Is Alive', 'type': ['boolean'], 'required': True},
                    'friends': {'title': 'Friends', 'type': ['array'], 'items': '$Person', 'required': True}
                }
            }
        },
        'fields': {
            '_id': {'title': ' Id', 'type': ['string', 'null'], 'default': None, 'required': False},
            'name': {'title': 'Name', 'type': ['string'], 'required': True},
            'person': {'type': ['$Person', 'null'], 'default': None, 'required': False},
            'books': {'title': 'Books', 'type': ['array'], 'items': '$Book', 'required': True},
            'is_male': {'title': 'Is Male', 'type': ['boolean', 'null'], 'required': True}
        }
    }

    """

    result = defaultdict(dict)
    result['title'] = schema['title']
    if '$defs' in schema:
        for sk, sv in schema['$defs'].items():
            result['$'][sk] = clean_model_schema(sv)

    for k, v in schema['properties'].items():
        result['fields'][k] = {}
        if 'title' in v:
            result['fields'][k]['title'] = v['title']

        if 'type' in v:
            result['fields'][k]['type'] = [v['type']]

        if 'anyOf' in v:
            result['fields'][k]['type'] = [i['type'] if 'type' in i else _ref_name(i['$ref']) for i in v['anyOf']]
            if 'array' in result['fields'][k]['type']:
                # One of them was array, so add the `items` field
                for t in v['anyOf']:
                    if 'items' in t:
                        result['fields'][k]['items'] = _ref_name(t['items']['$ref'])

        if 'default' in v:
            result['fields'][k]['default'] = v['default']

        if '$ref' in v:  # For obj
            result['fields'][k]['type'] = _ref_name(v['$ref'])

        if 'items' in v:  # For array
            result['fields'][k]['items'] = _ref_name(v['items']['$ref'])

        result['fields'][k]['required'] = k in schema.get('required', [])

    # Cast it to have a more clear stdout
    return dict(result)


def get_models():
    return [
        {
            'index': i,
            'name': model.__name__,
            'module': model.__module__,
        }
        for i, model in enumerate(config.MODELS)
    ]


def serialize_models(data: Any):
    if issubclass(type(data), BaseModel):
        return data.model_dump()

    elif isinstance(data, IterableDataTypes):
        return [serialize_models(d) for d in data]
