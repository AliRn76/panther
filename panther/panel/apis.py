from panther.app import API
from panther.configs import config


@API()
async def list_models():
    data = dict()
    for i, m in enumerate(config['models']):
        data['name'] = m['name']
        data['app'] = '.'.join(a for a in m['app'])
        data['path'] = m['path']
        data['index'] = i
    return data


@API()
async def model_list(index: int):
    model = config['models'][index]['class']
    return model.find()


@API()
async def model_retrieve(index: int, id: int):
    model = config['models'][index]['class']
    return model.find_one(id=id)


