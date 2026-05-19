# Configuration Reference

Panther loads configuration from the module passed to `Panther(..., configs=...)`. If no config module is provided, Panther tries to load `core.configs`.

In single-file apps, pass `configs=__name__`:

```python
from panther import Panther


url_routing = {}
app = Panther(__name__, configs=__name__, urls=url_routing)
```

In multi-file apps, define settings in `core/configs.py` and let `Panther(__name__)` load them.

## Common Settings

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `DATABASE` | `dict` | `{}` | Configures the database engine and query backend. |
| `REDIS` | `dict` | unset | Enables Redis for caching, throttling, token revocation, and WebSocket pub/sub. |
| `SECRET_KEY` | `str` | `None` | Secret used by JWT and encrypted PantherDB setups. |
| `AUTHENTICATION` | dotted path | `None` | Default HTTP authentication class. |
| `WS_AUTHENTICATION` | dotted path | `None` | Default WebSocket authentication class. |
| `JWT_CONFIG` | `dict` | `{}` | JWT key, algorithm, and token lifetimes. |
| `USER_MODEL` | dotted path | `panther.db.models.BaseUser` | User model used by built-in authentication. |
| `MIDDLEWARES` | `list` | `[]` | Global HTTP middleware classes or dotted paths. |
| `WS_MIDDLEWARES` | `list` | `[]` | Global WebSocket middleware classes or dotted paths. |
| `THROTTLING` | `Throttle` | `None` | Global request throttle. |
| `BACKGROUND_TASKS` | `bool` | `False` | Enables background task processing. |
| `TEMPLATES_DIR` | `str` or `list[str]` | `'.'` | Template lookup directory or directories. |
| `TIMEZONE` | `str` | `'UTC'` | Timezone name used by Panther utilities. |
| `LOG_QUERIES` | `bool` | `False` | Enables query logging. |
| `AUTO_REFORMAT` | `bool` | `False` | Runs Ruff formatting/check fixes when the app starts. |
| `URLs` | dotted path | required when `urls` is not passed | Points to the URL routing dictionary. |

Unknown uppercase config values are also copied onto `panther.configs.config`, so project-specific settings can be accessed through `config.MY_SETTING`.

## URLs

For single-file apps, pass routes directly:

```python
url_routing = {
    'health/': health_api,
}

app = Panther(__name__, configs=__name__, urls=url_routing)
```

For project-style apps, point `URLs` to a routing dictionary:

```python
URLs = 'core.urls.url_routing'
```

`URLs` should be a dotted string in config. If you already have the dictionary object, pass it directly to `Panther(..., urls=...)`.

## Database

PantherDB example:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.PantherDBConnection',
        'path': 'database.pdb',
    },
}
```

MongoDB example:

```python
DATABASE = {
    'engine': {
        'class': 'panther.db.connections.MongoDBConnection',
        'host': 'localhost',
        'port': 27017,
        'database': 'panther',
    },
}
```

You can override only the query backend with:

```python
DATABASE = {
    'query': 'path.to.CustomQuery',
}
```

## Redis

Redis is optional. Configure it when you need Redis-backed cache, throttling, token revocation, or WebSocket pub/sub.

```python
REDIS = {
    'class': 'panther.db.connections.RedisConnection',
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
}
```

The `redis` extra dependency is required.

## Authentication

Configure default HTTP authentication:

```python
AUTHENTICATION = 'panther.authentications.JWTAuthentication'
SECRET_KEY = 'change-me'
```

Configure default WebSocket authentication:

```python
WS_AUTHENTICATION = 'panther.authentications.QueryParamJWTAuthentication'
```

Endpoint-level `auth` overrides these defaults.

## JWT_CONFIG

`JWT_CONFIG` is needed when built-in JWT authentication is used. If `key` is omitted, Panther uses `SECRET_KEY`.

```python
from datetime import timedelta


SECRET_KEY = 'change-me'
JWT_CONFIG = {
    'key': SECRET_KEY,
    'algorithm': 'HS256',
    'life_time': timedelta(days=1),
    'refresh_life_time': timedelta(days=7),
}
```

`life_time` and `refresh_life_time` may be `timedelta` or integer seconds.

## User Model

By default, Panther uses `panther.db.models.BaseUser`.

Use `USER_MODEL` to point to your own model:

```python
USER_MODEL = 'app.models.User'
```

The user model is also added to `config.MODELS`.

## Middleware

HTTP middleware:

```python
MIDDLEWARES = [
    'panther.middlewares.cors.CORSMiddleware',
]
```

WebSocket middleware:

```python
WS_MIDDLEWARES = [
    'app.middlewares.MyWebsocketMiddleware',
]
```

Middleware entries may be classes or dotted import paths.

## CORS

When using `CORSMiddleware`, configure CORS settings in the same config module:

```python
ALLOW_ORIGINS = ['https://example.com']
ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
ALLOW_HEADERS = ['*']
ALLOW_CREDENTIALS = True
CORS_MAX_AGE = 3600
```

## Throttling

Use a global throttle:

```python
from datetime import timedelta

from panther.throttling import Throttle


THROTTLING = Throttle(rate=100, duration=timedelta(minutes=1))
```

Endpoint-level throttling overrides the global throttle.

## Templates

Use `TEMPLATES_DIR` for `TemplateResponse`.

```python
TEMPLATES_DIR = 'templates/'
```

If omitted, Panther uses the app base directory and Panther's packaged template folders for the admin panel and OpenAPI.

## Background Tasks

Enable background tasks:

```python
BACKGROUND_TASKS = True
```

Then schedule tasks with `BackgroundTask(...).submit()`. Prefer scheduling tasks during startup so the background task system is initialized.

## Timezone

Set a timezone name:

```python
TIMEZONE = 'UTC'
```

Panther utilities use this when generating timezone-aware datetimes.

## Logging Queries

Enable query logging:

```python
LOG_QUERIES = True
```

## Auto-Reformat

Enable Ruff auto-formatting:

```python
AUTO_REFORMAT = True
```

This runs Ruff when the app initializes. It is intended for development workflows; avoid surprising write operations in production.

## Custom Settings

Any unknown uppercase setting is copied to `config`.

```python
FEATURE_FLAG = True
```

Access it with:

```python
from panther.configs import config


if config.FEATURE_FLAG:
    ...
```
