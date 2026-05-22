# Architecture

This page explains Panther's internal flow at a high level. It is intended for maintainers and coding agents.

## Application Startup

`Panther` is defined in `panther/main.py`.

When an app is created, Panther:

- Stores the provided config module name and URL dictionary.
- Sets `config.BASE_DIR`.
- Loads config values from the provided module or `core.configs`.
- Loads Redis, timezone, database, secret key, throttling, user model, templates, middleware, background tasks, URLs, authentication, and WebSocket connections.
- Validates endpoint inheritance.
- Prints runtime info.

The global config object lives in `panther/configs.py`. This keeps simple apps ergonomic, but it also means tests and multi-app processes must be careful with shared state.

## ASGI Dispatch

`Panther.__call__` receives the ASGI `scope`, `receive`, and `send` callables.

- `scope['type'] == 'http'` goes to `handle_http`.
- `scope['type'] == 'websocket'` goes to `handle_ws`.
- `scope['type'] == 'lifespan'` runs startup events and starts the WebSocket connection listener when needed.

## HTTP Request Flow

The HTTP path is:

1. Create `Request`.
2. Read the request body.
3. Build the global HTTP middleware chain.
4. Resolve the endpoint with `find_endpoint`.
5. Collect path variables.
6. Dispatch to a function-based API or class-based API.
7. Convert errors into `Response` objects.
8. Send response headers and body.

The central files are:

- `panther/main.py`
- `panther/request.py`
- `panther/base_request.py`
- `panther/routings.py`
- `panther/app.py`
- `panther/response.py`

## Endpoint Execution

Function APIs are created with `@API(...)`. Class APIs inherit from `GenericAPI`.

For function APIs, `API.__call__` wraps the function and stores endpoint metadata for routing and OpenAPI.

For class APIs, `GenericAPI.call_method` selects the method matching the HTTP verb and delegates through an `API` wrapper so class-based and function-based endpoints share behavior.

Endpoint handling order is:

1. Check HTTP method.
2. Run authentication.
3. Run permissions.
4. Run throttling.
5. Validate input model for `POST`, `PUT`, and `PATCH`.
6. Read cached response for cached `GET` endpoints.
7. Build endpoint keyword arguments from path variables and request annotations.
8. Call the endpoint.
9. Wrap plain data in `Response`.
10. Apply output model and pagination.
11. Store cached response for cached `GET` endpoints.

## Routing

Routes are declared as dictionaries. `panther/routings.py`:

- Flattens nested URL dictionaries.
- Validates URL keys and endpoints.
- Converts flat URLs back into nested dictionaries.
- Checks ambiguous same-level path variables.
- Resolves incoming paths with static dictionary lookups and dynamic path-variable fallbacks.

Path variables use angle brackets, for example `books/<book_id>/`.

## Request Parsing

`Request` extends `BaseRequest`.

`BaseRequest` provides:

- headers
- query params
- path
- client/server address
- scheme
- HTTP version
- path variable collection and casting

`Request` adds:

- HTTP method
- body reading
- parsed `data`
- `validated_data`
- input-model validation

Request body parsing supports JSON, `application/x-www-form-urlencoded`, multipart form data, and raw bytes for unsupported content types.

## Response Sending

`Response` stores Python data, status code, headers, pagination, and cookies.

When sent, it:

- Serializes `data` to bytes with `orjson` unless data is already bytes or `None`.
- Adds `Content-Length`.
- Sends `http.response.start`.
- Sends `http.response.body`.

Specialized responses include:

- `HTMLResponse`
- `PlainTextResponse`
- `StreamingResponse`
- `FileResponse`
- `TemplateResponse`
- `RedirectResponse`

## Middleware

HTTP middleware inherits from `HTTPMiddleware`; WebSocket middleware inherits from `WebsocketMiddleware`.

Global HTTP middleware is loaded from the `MIDDLEWARES` config. WebSocket middleware is loaded from `WS_MIDDLEWARES`.

Endpoint-level middleware can be passed to `API(..., middlewares=[...])` or set on `GenericAPI`.

Middleware receives a dispatch callable and returns a response or connection.

## Authentication And Permissions

HTTP authentication and permissions run inside `API.handle_endpoint`.

WebSocket authentication and permissions run inside `WebsocketConnections.listen`.

Built-in HTTP permissions include:

- `IsAuthenticated`
- `IsAuthenticatedOrReadonly`

Built-in authentication classes are JWT-based and live in `panther/authentications.py`.

## WebSocket Flow

WebSocket endpoints inherit from `GenericWebsocket`.

Flow:

1. Create a temporary `Websocket` connection object.
2. Build the WebSocket middleware chain.
3. Resolve the endpoint.
4. Convert the temporary connection into the endpoint class.
5. Collect path variables.
6. Run authentication and permissions.
7. Call `connect`.
8. Require the endpoint to call `accept` or `close`.
9. Listen for incoming messages and call `receive`.
10. Remove the connection on disconnect.

`send_message_to_websocket` publishes messages to the connection registry. Redis is used when configured; otherwise Panther uses a multiprocessing manager.

## Events And Background Tasks

Events live in `panther/events.py`.

- `Event.startup` registers startup hooks.
- `Event.shutdown` registers shutdown hooks.
- Startup hooks run during ASGI lifespan startup.
- Shutdown hooks run from Panther cleanup.

Background tasks live in `panther/background_tasks.py`.

Enable them with:

```python
BACKGROUND_TASKS = True
```

Then schedule tasks with `BackgroundTask(...).submit()`.

## Database Layer

Models inherit from `panther.db.Model`, which combines Pydantic models with Panther's query interface.

Database connection classes live in `panther/db/connections.py`.

Supported built-in engines:

- `PantherDBConnection`
- `MongoDBConnection`

Query behavior is implemented under `panther/db/queries/`.

## Testing Architecture

`panther/test.py` provides:

- `APIClient`
- `WebsocketClient`

The test runner in `tests/__main__.py` runs test files individually because global config and model registration can otherwise leak between tests.

Use:

```bash
python tests --not_mongodb --not_slow
```

when MongoDB or slow integration paths are not needed.

## Performance-Sensitive Areas

Panther's hot path is intentionally small. Be careful when changing:

- request body reading
- response serialization
- middleware chain creation
- class-based API dispatch
- route lookup
- headers and cookie handling
- caching
- request and response object allocation

Prefer startup-time validation and precomputation where possible, and avoid adding per-request work unless it is required for every request.
