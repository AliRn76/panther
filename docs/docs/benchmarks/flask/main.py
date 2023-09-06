import json

from flask import Flask, Response, request

app = Flask(__name__)


# Fake API
def fake_api(*args, **kwargs):
    return Response(
        response=json.dumps({'detail': 'Ok'}),
        status=202,
        content_type='application/json'
    )


# Pre Routing
for n in range(50):
    app.route(f'/users/<user>/{n}')(fake_api)


# Main API
@app.route('/users/<user>/records/<record>', methods=['PUT'])
async def main_api(user, record):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if not request.headers.get('authorization'):
        return Response(
            response=json.dumps({'detail': 'Authorization Error'}),
            status=401,
            content_type='application/json'
        )

    query_params = dict()
    if request.query_string != b'':
        query_string = request.query_string.decode('utf-8').split('&')
        for param in query_string:
            k, v = param.split('=')
            query_params[k] = v

    data = {
        'params': {'user': user, 'record': record},
        'query': query_params,
        'data': json.loads(request.data.decode() or '{}')
    }
    return Response(
        response=json.dumps(data),
        status=200,
        content_type='application/json'
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
