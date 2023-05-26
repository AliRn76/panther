from panther.app import API
from panther.configs import config


@API()
async def list_models():
    for i, m in enumerate(config['models']):
        m.pop('class')
        m['app'] = '.'.join(a for a in m['app'])
        m['index'] = i
    return config['models']


@API()
async def model_list(index: int):
    model = config['models'][index]['class']
    return model.find()


@API()
async def model_retrieve(index: int, id: int):
    model = config['models'][index]['class']
    return model.find_one(id=id)


