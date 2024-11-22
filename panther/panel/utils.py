from collections import defaultdict

from panther.configs import config
from panther.db.models import Model


def _ref_name(ref: str) -> str:
    obj_name = ref.rsplit('/', maxsplit=1)[1]
    return f'${obj_name}'


def clean_model_schema(schema: dict) -> dict:
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
        elif 'anyOf' in v:
            result['fields'][k]['type'] = [i['type'] if 'type' in i else _ref_name(i['$ref']) for i in v['anyOf']]
        if 'default' in v:
            result['fields'][k]['default'] = v['default']

        if '$ref' in v:  # For obj
            result['fields'][k]['type'] = _ref_name(v['$ref'])

        if 'items' in v:  # For array
            result['fields'][k]['items'] = _ref_name(v['items']['$ref'])

        result['fields'][k]['required'] = k in schema['required']
    return result


# TODO: Remove this
def get_model_fields(model):
    result = {}

    for k, v in model.model_fields.items():
        try:
            is_model = issubclass(v.annotation, Model)
        except TypeError:
            is_model = False

        if is_model:
            result[k] = get_model_fields(v.annotation)
        else:
            result[k] = getattr(v.annotation, '__name__', str(v.annotation))
    return result


def get_models():
    return [{
        'index': i,
        'name': model.__name__,
        'module': model.__module__,
    } for i, model in enumerate(config.MODELS)]
