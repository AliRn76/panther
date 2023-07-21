from panther.app import API
from panther.configs import config


@API()
async def list_models():
    result = list()
    for i, m in enumerate(config['models']):
        data = dict()
        data['name'] = m['name']
        data['app'] = '.'.join(a for a in m['app'])
        data['path'] = m['path']
        data['index'] = i
        result.append(data)
    return result


@API()
async def model_list(index: int):
    model = config['models'][index]['class']
    result ={
        'fields': {k: getattr(v.annotation, '__name__', str(v.annotation)) for k, v in model.model_fields.items()},
    }
    if data := model.find():
        result['data'] = data
    else:
        result['data'] = []
    return result


@API()
async def model_retrieve(index: int, id: int):
    model = config['models'][index]['class']
    return model.find_one(id=id)


