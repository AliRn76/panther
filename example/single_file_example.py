from panther import Panther
from panther.app import API


@API()
async def hello_world_api():
    return {'detail': 'Hello World'}

url_routing = {
    '/': hello_world_api,
}

app = Panther(__name__, configs=__name__, urls=url_routing)

@app.on_event('startup')
def startup():
    print('Its startup')


@app.on_event('shutdown')
def shutdown():
    print('Its shutdown')
