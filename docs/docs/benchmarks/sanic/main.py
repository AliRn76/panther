from sanic import Sanic
from sanic.response import empty

app = Sanic('TEST')


@app.get('/')
async def hello_world(request):
    return empty(status=200)
