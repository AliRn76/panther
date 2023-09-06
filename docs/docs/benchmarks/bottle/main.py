import json

from bottle import Bottle, HTTPResponse, request

app = Bottle()


# Fake API
def fake_api(*args, **kwargs):
    return HTTPResponse(body={'detail': 'Ok'}, status=202)


# Pre Routing
for n in range(50):
    app.route(f'users/<user>/{n}')(fake_api)


# Main API
@app.route('/users/<user>/records/<record>', method=['PUT'])
def main_api(user, record):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if not request.headers.get('Authorization'):
        return HTTPResponse(body={'detail': 'Authorization Error'}, status=401)

    data = {
        'params': {'user': user, 'record': record},
        'query': dict(request.query),
        'data': json.loads(request.body.read().decode() or '{}'),
    }
    return HTTPResponse(body=data, status=200)


# Post Routing
for n in range(50):
    app.route(f'fake-route-{n}/<part>')(fake_api)
