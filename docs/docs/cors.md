# CORSMiddleware

`CORSMiddleware` is a middleware for Panther applications that handles Cross-Origin Resource Sharing (CORS). It
automatically adds the appropriate CORS headers to all HTTP responses based on your configuration, and handles
preflight (OPTIONS) requests.

## Purpose

CORS is a security feature implemented by browsers to restrict web applications running on one origin from interacting
with resources from a different origin. `CORSMiddleware` makes it easy to configure and manage CORS policies in your
Panther application.

## Configuration Options

Set the following variables in your Panther config file (e.g., `core/configs.py`) to control CORS behavior:

| Config Variable     | Type      | Description                                                          | Default                                                |
|---------------------|-----------|----------------------------------------------------------------------|--------------------------------------------------------|
| _ALLOW_ORIGINS_     | list[str] | List of allowed origins. Use `["*"]` to allow all origins.           | `["*"]`                                                |
| _ALLOW_METHODS_     | list[str] | List of allowed HTTP methods.                                        | `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]` |
| _ALLOW_HEADERS_     | list[str] | List of allowed request headers. Use `["*"]` to allow all headers.   | `["*"]`                                                |
| _ALLOW_CREDENTIALS_ | bool      | Whether to allow credentials (cookies, authorization headers, etc.). | `False`                                                |
| _EXPOSE_HEADERS_    | list[str] | List of headers that can be exposed to the browser.                  | `[]`                                                   |
| _CORS_MAX_AGE_      | int       | Number of seconds browsers can cache preflight responses.            | `600`                                                  |

## Usage

1. Set the desired CORS config variables in your config file.
2. Add `'panther.middlewares.cors.CORSMiddleware'` to your `MIDDLEWARES` list.

### Example Configuration

```python title="e.g. core/configs.py"
ALLOW_ORIGINS = ["https://example.com", "https://another.com"]
ALLOW_METHODS = ["GET", "POST"]
ALLOW_HEADERS = ["Content-Type", "Authorization"]
ALLOW_CREDENTIALS = True
EXPOSE_HEADERS = ["X-Custom-Header"]
CORS_MAX_AGE = 3600

MIDDLEWARES = [
    # ... other middlewares ...
    'panther.middlewares.cors.CORSMiddleware',
]
```

## How It Works

- For every request, the middleware adds the appropriate CORS headers to the response.
- For preflight (OPTIONS) requests, it returns a 204 response with the necessary headers.
- The headers are set based on your configuration, with sensible defaults if not specified.

## Notes

- If you set `ALLOW_ORIGINS = ["*"]`, all origins are allowed.
- If you set `ALLOW_HEADERS = ["*"]`, all headers are allowed.
- If `ALLOW_CREDENTIALS` is `True`, the `Access-Control-Allow-Credentials` header is set to `true`.
- If you specify `EXPOSE_HEADERS`, those headers will be exposed to the browser.

For more details, see the source code in `panther/middlewares/cors.py`.

---

For a deeper understanding of CORS, you may also want to check
the [MDN Web Docs CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS).
