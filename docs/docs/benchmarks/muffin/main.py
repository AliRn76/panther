import json
from muffin import Application, ResponseJSON


app = Application(debug=True)


# Fake API
async def fake_api(*args, **kwargs):
    return ResponseJSON(content={'detail': 'Ok'}, status_code=202)

# Pre Routing
for n in range(50):
    app.route(f'users/{{user:int}}/{n}')(fake_api)


# Main API
@app.route('/users/{user:int}/records/{record:int}', methods=['PUT'])
async def main_api(request):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if not request.headers.get('authorization'):
        return ResponseJSON(content={'detail': 'Authorization Error'}, status_code=401)

    body = await request.body()
    data = {
        'params': request.path_params,
        'query': dict(request.url.query),
        'data': json.loads(body.decode() or '{}')
    }
    return ResponseJSON(content=data, status_code=200)

# Post Routing
for n in range(50):
    app.route(f'fake-route-{n}/{{part:int}}')(fake_api)
