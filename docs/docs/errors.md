# Error Handling

Panther converts `APIError` exceptions into HTTP responses. Unknown exceptions are logged and returned as `500 Internal Server Error`.

Error classes live in `panther.exceptions`.

## APIError

Use `APIError` when you need a custom API error.

```python
from panther import status
from panther.exceptions import APIError


async def endpoint():
    raise APIError(
        detail={'detail': 'Something went wrong'},
        status_code=status.HTTP_400_BAD_REQUEST,
        headers={'X-Error-Code': 'example'},
    )
```

Panther returns:

- `detail` as response data.
- `status_code` as the HTTP status.
- `headers` as response headers.

If `detail` is a string, Panther wraps it as `{'detail': detail}`.

## Built-In API Errors

| Exception | Status | Default detail |
| --- | ---: | --- |
| `APIError` | 500 | `Internal Server Error` |
| `BadRequestAPIError` | 400 | `Bad Request` |
| `RequestEntityTooLargeAPIError` | 413 | `Request Entity Too Large` |
| `AuthenticationAPIError` | 401 | `Authentication Error` |
| `AuthorizationAPIError` | 403 | `Permission Denied` |
| `NotFoundAPIError` | 404 | `Not Found` |
| `MethodNotAllowedAPIError` | 405 | `Method Not Allowed` |
| `UnprocessableEntityError` | 422 | `Unprocessable Entity Error` |
| `UpgradeRequiredError` | 426 | `This service requires use of the WebSocket protocol.` |
| `ThrottlingAPIError` | 429 | `Too Many Request` |

Example:

```python
from panther.exceptions import BadRequestAPIError


async def create_item():
    raise BadRequestAPIError(detail='Name is required')
```

## Not Found

For database models, `find_one_or_raise` raises `NotFoundAPIError`.

```python
from app.models import Book


async def get_book(book_id: str):
    return await Book.find_one_or_raise(id=book_id)
```

Pass filters as keyword arguments or dictionaries. Do not pass a raw ID string positionally.

## Authentication And Authorization

Use `AuthenticationAPIError` for invalid credentials.

```python
from panther.exceptions import AuthenticationAPIError


class ApiKeyAuthentication:
    async def __call__(self, request):
        if request.headers['x-api-key'] != 'secret':
            raise AuthenticationAPIError
        return {'username': 'admin'}
```

Use permissions for authorization checks. Returning `False` from a permission causes `AuthorizationAPIError`.

```python
class IsAdmin:
    async def __call__(self, request):
        return bool(request.user and request.user.get('is_admin'))
```

## Validation Errors

When `input_model` validation fails, Panther returns `BadRequestAPIError`.

```python
from pydantic import BaseModel, Field

from panther.app import API
from panther.request import Request


class CreateBookInput(BaseModel):
    title: str = Field(min_length=1)


@API(methods=['POST'], input_model=CreateBookInput)
async def create_book(request: Request):
    return request.validated_data.model_dump()
```

Invalid JSON raises `UnprocessableEntityError`.

## Preserving APIError Status Codes

When catching broad exceptions, re-raise `APIError` before converting unknown exceptions to `500`.

```python
from panther import status
from panther.exceptions import APIError


async def upload_file():
    try:
        raise APIError('File too large', status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    except APIError:
        raise
    except Exception as e:
        raise APIError(
            detail=f'Upload failed: {e}',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
```

Without the `except APIError: raise` branch, intentional API errors can be accidentally converted into `500` responses.

## RedirectAPIError

`RedirectAPIError` is an exception-based redirect helper.

```python
from panther.exceptions import RedirectAPIError


async def old_endpoint():
    raise RedirectAPIError('/new-endpoint/')
```

For normal endpoint code, prefer `RedirectResponse` when returning a redirect is clearer.

## WebSocket Errors

`WebsocketError` is the base WebSocket error class. WebSocket close codes are available in `panther.status`.

```python
from panther import status
from panther.websocket import close_websocket_connection


async def close_connection(connection_id: str):
    await close_websocket_connection(
        connection_id=connection_id,
        code=status.WS_1008_POLICY_VIOLATION,
        reason='Policy violation',
    )
```

## Framework And Database Errors

`PantherError` and `DatabaseError` are internal/setup-level errors. They are not regular API response helpers:

- `PantherError` is used for invalid configuration, routing, imports, and setup.
- `DatabaseError` is used by database/query internals.

Use `APIError` subclasses for user-facing endpoint errors.
