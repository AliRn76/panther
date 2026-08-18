# LLM Context

This page is a compact Panther reference for LLMs and coding agents. Prefer it together with `AGENTS.md`, `examples/canonical/`, and the source code under `panther/`.

## What Panther Is

Panther is a Python 3.10+ async ASGI web framework for building APIs. It provides:

- Function-based APIs with `@API(...)`.
- Class-based APIs with `GenericAPI`.
- URL routing through nested dictionaries.
- Request parsing and response classes.
- Pydantic input validation and output filtering.
- OpenAPI documentation views.
- WebSockets with `GenericWebsocket`.
- Middleware, authentication, permissions, throttling, caching, events, background tasks, templates, file handling, and database integrations.

## Main Modules

- `panther/main.py` defines `Panther`, the ASGI application.
- `panther/app.py` defines `API` and `GenericAPI`.
- `panther/routings.py` validates and resolves URL dictionaries.
- `panther/request.py` and `panther/base_request.py` define request objects, headers, query params, path variables, and body parsing.
- `panther/response.py` defines `Response`, `HTMLResponse`, `PlainTextResponse`, `StreamingResponse`, `FileResponse`, `TemplateResponse`, and `RedirectResponse`.
- `panther/websocket.py` and `panther/base_websocket.py` define WebSocket endpoint behavior.
- `panther/serializer.py` defines `ModelSerializer`.
- `panther/db/` defines models, connections, cursors, and query backends.
- `panther/generics.py` defines reusable CRUD-style API base classes.
- `panther/test.py` defines `APIClient` and `WebsocketClient`.

## Minimal App

```python
from panther import Panther
from panther.app import API


@API()
async def hello():
    return {'message': 'Hello from Panther'}


url_routing = {
    '': hello,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
```

Run with:

```bash
panther run main:app
```

That is an alias for Uvicorn. Panther also has an optional Rust web server (hyper + tokio through
PyO3), installed with `pip install panther[rust]` and selected with
`panther run --server rust main:app`, or from Python with `panther.server.run(app)`. It is opt-in —
never assume it is installed. See [Rust Web Server](rust_server.md).

## Function APIs

Use `@API(...)` on a function. Panther injects path variables by name and injects `Request` when the function annotation asks for it.

```python
from pydantic import BaseModel

from panther.app import API
from panther.request import Request
from panther.response import Response


class CreateBookInput(BaseModel):
    title: str
    pages_count: int


@API(methods=['POST'], input_model=CreateBookInput)
async def create_book(request: Request):
    data = request.validated_data
    return Response(data=data.model_dump(), status_code=201)


@API(methods=['GET'])
async def get_book(book_id: int):
    return {'book_id': book_id}
```

## Class APIs

Use `GenericAPI` when one URL supports multiple HTTP methods.

```python
from panther.app import GenericAPI
from panther.request import Request


class NotesAPI(GenericAPI):
    async def get(self):
        return [{'id': 1, 'text': 'hello'}]

    async def post(self, request: Request):
        return {'created': request.data}
```

## Routing

Routes are dictionaries. Nested dictionaries are supported. Path variables use angle brackets.

```python
url_routing = {
    'books/': list_books,
    'books/<book_id>/': get_book,
    'admin/': {
        'users/': users_api,
    },
}
```

Panther validates URL structure at startup and resolves routes through a nested dictionary.

## Request Object

Common request attributes:

- `request.method`
- `request.path`
- `request.headers`
- `request.query_params`
- `request.data`
- `request.validated_data`
- `request.path_variables`
- `request.user`
- `request.client`
- `request.server`

`request.data` lazily parses JSON, form data, multipart data, or returns raw bytes for unknown content types.

## Responses

Return either a `Response` object or plain serializable data. Plain data is wrapped in `Response`.

```python
from panther.response import HTMLResponse, Response


async def api():
    return Response(data={'ok': True})


async def html():
    return HTMLResponse('<h1>Hello</h1>')
```

Use `StreamingResponse` for generators, `FileResponse` for files, `TemplateResponse` for Jinja templates, and `RedirectResponse` for redirects.

## Validation And Serialization

Use Pydantic models or `ModelSerializer` as `input_model`. Validated input is available as `request.validated_data`.

Use `output_model` to filter response data.

```python
@API(methods=['POST'], input_model=InputModel, output_model=OutputModel)
async def endpoint(request: Request):
    return request.validated_data.model_dump()
```

## Auth, Permissions, Throttling, Cache

`API` and `GenericAPI` support:

- `auth`
- `permissions`
- `throttling`
- `cache`
- `middlewares`

Authentication callables must be async and receive the request. Permission callables must be async and return `True` or `False`.

```python
@API(auth=ApiKeyAuthentication, permissions=[IsAdmin])
async def private_endpoint(request: Request):
    return {'user': request.user}
```

## WebSockets

Use `GenericWebsocket`. WebSocket support requires the optional `websockets` dependency.

```python
from panther.websocket import GenericWebsocket


class EchoWebsocket(GenericWebsocket):
    async def connect(self):
        await self.accept()

    async def receive(self, data: str | bytes):
        await self.send(f'Echo: {data}')
```

## Database

Define models by inheriting from `panther.db.Model`. Configure a database engine in configs.

```python
from panther.db import Model


class Book(Model):
    title: str
    pages_count: int
```

Panther supports PantherDB and MongoDB query backends. Common methods include `insert_one`, `find`, `find_one`, `find_one_or_raise`, `exists`, `update`, and `delete`.

## Testing

Use `APIClient` and `WebsocketClient` from `panther.test`.

```python
from panther.test import APIClient


async def test_health():
    client = APIClient(app=app)
    response = await client.get('/health/')
    assert response.status_code == 200
```

`WebsocketClient.connect()` is synchronous and returns the ASGI events the endpoint sent.

```python
from panther.test import WebsocketClient


def test_echo():
    messages = WebsocketClient(app=app).connect('/ws/echo/')
    assert messages[0]['type'] == 'websocket.accept'
```

## Common Gotchas

- Prefer `examples/canonical/` for generated code patterns.
- Do not use stale generated Q&A as source of truth.
- WebSocket examples need optional dependencies.
- Blog example needs its local `requirements.txt`.
- Panther uses global config state, so tests often call `config.refresh()`.
- Avoid inventing `TestClient`; the built-in clients are `APIClient` and `WebsocketClient`.
- Avoid inventing serializer `Field`; `ModelSerializer` is Pydantic-based.
- Use `find_one_or_raise(id=value)`, not a positional string.
