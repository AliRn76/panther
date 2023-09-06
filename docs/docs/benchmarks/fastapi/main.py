import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse


app = FastAPI()


# Fake API
async def fake_api(*args, **kwargs):
    return HTMLResponse(content={'detail': 'Ok'}, status_code=202)


# Pre Routing
for n in range(50):
    app.get(f'users/{{user}}/{n}')(fake_api)


# Main API
@app.put('/users/{user}/records/{record}')
async def main_api(request: Request, user: int, record: int):
    """
    1. Check Method
    2. Check Authorization Header
    3. Read Body
    4. Read Query Params
    5. Read Path Variables
    6. Return Json Response
    """
    if not request.headers.get('Authorization'):
        return JSONResponse(content={'detail': 'Authorization Error'}, status_code=401)

    body = await request.body()
    data = {
        'params': {'user': user, 'record': record},
        'query': dict(request.query_params),
        'data': json.loads(body.decode() or '{}'),
    }
    return JSONResponse(content=data, status_code=200)


# Post Routing
for n in range(50):
    app.get(f'fake-route-{n}/{{part}}')(fake_api)
