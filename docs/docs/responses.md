# Responses

Panther response classes live in `panther.response`. Endpoints can return a `Response` instance or plain serializable data. Plain data is automatically wrapped in `Response`.

## Response

`Response` is the default JSON response.

```python
from panther import status
from panther.response import Response


async def get_status():
    return Response(
        data={'status': 'ok'},
        status_code=status.HTTP_200_OK,
        headers={'X-App': 'panther'},
    )
```

Supported JSON response data includes dictionaries, lists, tuples, sets, cursors, Pydantic models, primitive values, bytes, and `None`.

Panther uses `orjson` for JSON serialization. `Content-Type` defaults to `application/json`, and `Content-Length` is added when the response is sent.

Response bytes are created lazily and reused for headers and sending. Finish processing a response before accessing `response.body`; assigning a new `response.data` value creates new bytes, but in-place mutations of an already rendered container are not tracked.

## Returning Plain Data

You can return plain serializable data from an API. Panther wraps it in `Response`.

```python
from panther.app import API


@API()
async def hello():
    return {'message': 'Hello from Panther'}
```

Use an explicit `Response` when you need a custom status code, headers, cookies, pagination, or a specialized response class.

## Headers

Pass headers with the `headers` argument.

```python
from panther.response import Response


async def with_headers():
    return Response(
        data={'ok': True},
        headers={'X-Request-Source': 'example'},
    )
```

Header values are converted to bytes when the response is sent.

## Cookies

Use `Cookie` and pass one cookie or a list of cookies with `set_cookies`.

```python
from panther.response import Cookie, Response


async def login():
    cookie = Cookie(
        key='session_id',
        value='abc123',
        httponly=True,
        secure=True,
        samesite='lax',
        max_age=3600,
    )
    return Response(data={'logged_in': True}, set_cookies=cookie)
```

`Cookie` supports:

- `key`
- `value`
- `path`
- `domain`
- `max_age`
- `secure`
- `httponly`
- `samesite`

## HTMLResponse

Use `HTMLResponse` for HTML strings.

```python
from panther.response import HTMLResponse


async def page():
    return HTMLResponse('<h1>Hello Panther</h1>')
```

`Content-Type` is `text/html; charset=utf-8`.

## PlainTextResponse

Use `PlainTextResponse` for text.

```python
from panther.response import PlainTextResponse


async def text():
    return PlainTextResponse('Hello Panther')
```

`Content-Type` is `text/plain; charset=utf-8`.

## StreamingResponse

Use `StreamingResponse` for sync or async generators.

```python
import asyncio

from panther.response import StreamingResponse


async def stream_numbers():
    async def numbers():
        for number in range(3):
            await asyncio.sleep(1)
            yield {'number': number}

    return StreamingResponse(numbers())
```

`StreamingResponse` sends chunks with `more_body=True` until the generator finishes. Bytes are sent as-is; other values are JSON-serialized.

## FileResponse

Use `FileResponse` to return a file relative to `config.BASE_DIR`.

```python
from panther.response import FileResponse


async def download():
    return FileResponse('files/report.pdf')
```

If the file does not exist, Panther returns a `404` JSON response. If the file exists, Panther detects the MIME type and reads the file bytes into the response.

## TemplateResponse

Use `TemplateResponse` for Jinja templates.

```python
from panther.response import TemplateResponse


async def profile():
    return TemplateResponse(
        name='profile.html',
        context={'username': 'ali'},
    )
```

Configure template lookup with:

```python
TEMPLATES_DIR = 'templates/'
```

You can also render an inline template string:

```python
from panther.response import TemplateResponse


async def inline_template():
    return TemplateResponse(source='<h1>Hello {{ name }}</h1>', context={'name': 'Panther'})
```

## RedirectResponse

Use `RedirectResponse` for redirects.

```python
from panther.response import RedirectResponse


async def old_path():
    return RedirectResponse('/new-path/')
```

The default status code is `307 Temporary Redirect`. You can pass another redirect status code with `status_code`.

## Output Models

Use `output_model` on `API` or `GenericAPI` to filter response data.

```python
from pydantic import BaseModel

from panther.app import API


class UserOutput(BaseModel):
    username: str


@API(output_model=UserOutput)
async def user_api():
    return {'username': 'ali', 'password': 'hidden'}
```

The response data becomes:

```json
{"username": "ali"}
```

If the output model has an async `to_response(instance, data)` method, Panther calls it to customize the serialized response.

## Pagination

`Response` accepts a `pagination` object. Generic list APIs use this to wrap results with:

- `count`
- `next`
- `previous`
- `results`

For most CRUD-style list endpoints, prefer `ListAPI` with `pagination = Pagination`.

## Best Practices

- Return plain data for simple JSON responses.
- Use `Response` when you need status codes, headers, cookies, or pagination.
- Use `HTMLResponse`, `PlainTextResponse`, `TemplateResponse`, `FileResponse`, `StreamingResponse`, and `RedirectResponse` when the content is not regular JSON.
- Prefer async generators for streaming examples.
- Be careful with large files: `FileResponse` reads the file into memory.
