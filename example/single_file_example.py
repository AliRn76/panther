from panther import Panther
from panther.app import API


@API()
async def hello_world_api():
    return {'detail': 'Hello World'}


url_routing = {
    '/': hello_world_api,
}


def startup():
    print('Its startup')


def shutdown():
    print('Its shutdown')


app = Panther(__name__, configs=__name__, urls=url_routing, startup=startup, shutdown=shutdown)
