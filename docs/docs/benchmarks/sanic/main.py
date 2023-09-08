from sanic import Sanic
from sanic.response import json


app = Sanic(__name__)


# Fake API
async def fake_api(*args, **kwargs):
    return json(body={'detail': 'Ok'}, status=202)


# Pre Routing
for n in range(50):
    app.route(f'users/<user:int>/{n}', name=f'pre-{n}')(fake_api)


# Main API
@app.route('/users/<user:int>/records/<record:int>', methods=['PUT'])
async def api(request, user, record):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if request.headers.get('authorization') is None:
        return json(body={'detail': 'Authorization Error'}, status=401)

    data = {
        'params': {'user': user, 'record': record},
        'query': dict(request.query_args),
        'data': request.json
    }
    return json(body=data, status=200)

# Post Routing
for n in range(50):
    app.route(f'fake-route-{n}/<part:int>', name=f'post-{n}')(fake_api)
