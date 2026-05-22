# Canonical Panther Examples

These examples are small, accurate reference apps for humans and LLM coding agents. Each file focuses on one Panther concept and can be run directly with:

```bash
panther run examples.canonical.01_single_file:app
```

If you run from a checkout without installing Panther globally, activate the project virtual environment first:

```bash
source .venv/bin/activate
```

WebSocket examples require Panther's optional WebSocket dependency:

```bash
pip install "panther[full]"
```

## Files

- `01_single_file.py` - Minimal app with a plain `Response`.
- `02_function_api.py` - Function-based APIs, path variables, query params, input validation, and output filtering.
- `03_class_api.py` - Class-based `GenericAPI` endpoints.
- `04_auth_permissions.py` - Custom authentication and permission classes.
- `05_middleware_cache_throttle.py` - Global middleware, endpoint cache, and throttling.
- `06_websocket.py` - Minimal `GenericWebsocket` echo endpoint.
- `07_files_streaming_templates.py` - HTML, template, file, redirect, and streaming responses.
- `08_pantherdb_models.py` - PantherDB model, serializer, and CRUD-style endpoints.
- `09_testing_clients.py` - Using `APIClient` and `WebsocketClient`.
- `10_events_background_tasks.py` - Startup/shutdown events and background task scheduling.

Prefer these files over older generated Q&A material when teaching an LLM Panther APIs.
