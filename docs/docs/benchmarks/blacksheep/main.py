from blacksheep import Application
from blacksheep.server.responses import json, unauthorized


app = Application()


# Fake API
async def fake_api():
    return json(data={'detail': 'Ok'}, status=202)


# Pre Routing
for n in range(50):
    app.route(f'users/<user>/{n}')(fake_api)


# Main API
@app.route('/users/<user>/records/<record>', methods=['PUT'])
async def view_api(request):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if not request.headers.get(b'authorization'):
        return unauthorized(message={'detail': 'Authorization Error'})

    data = {
        'params': request.route_values,
        'query': dict(request.query),
        'data': await request.json(),
    }
    return json(data=data, status=200)

# Post Routing
for n in range(50):
    app.route(f'fake-route-{n}/<part>')(fake_api)
