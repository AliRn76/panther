# AGENTS.md

## Project Overview

Panther is a Python 3.10+ async web framework focused on speed, simplicity, and practical API development. It is an ASGI framework with routing, request/response primitives, class-based and function-based APIs, OpenAPI support, WebSockets, middleware, authentication, permissions, throttling, caching, background tasks, templates, and database integrations.

When working in this repository, optimize for correctness first, then simplicity, then performance. Panther wants to stay small and fast, so prefer direct code paths and avoid adding abstraction unless it clearly reduces complexity.

## Repository Map

- `panther/` contains the framework source code.
- `panther/main.py` is the ASGI application entrypoint and request dispatcher.
- `panther/app.py` contains `API` and `GenericAPI` endpoint handling.
- `panther/routings.py` contains URL flattening, validation, and endpoint lookup.
- `panther/request.py` and `panther/base_request.py` define request parsing and request metadata.
- `panther/response.py` defines response classes, serialization, streaming, templates, redirects, and files.
- `panther/db/` contains database connections, models, cursors, and query backends.
- `panther/openapi/` contains OpenAPI schema and documentation views.
- `panther/panel/` contains the built-in admin panel.
- `panther/cli/` contains command-line tooling.
- `panther/server.py` drives an ASGI app on the optional Rust web server (lifespan, accept loop, graceful drain).
- `rust/` contains the optional Rust web server: a PyO3 extension built on hyper and tokio, packaged separately as `panther-server`.
- `tests/` contains the test suite.
- `docs/docs/` contains documentation pages.
- `examples/` contains example Panther applications.

## Development Setup

Use Python 3.10 or newer.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Some tests need external services:

```bash
docker run --rm -p 27017:27017 -d --name mongo mongo
docker run --rm -p 6379:6379 -d --name redis redis
```

The Rust web server is optional and not needed for most work. To build it you need a
[Rust toolchain](https://rustup.rs):

```bash
pip install maturin
maturin develop --release -m rust/Cargo.toml
```

Without it, the socket-level tests in `tests/test_rust_server.py` skip and everything else runs
unchanged. Keep it that way: `pip install panther` must never require a Rust toolchain.

## Test Commands

Prefer the project test runner because it runs test files individually for better isolation:

```bash
python tests
```

Useful variants:

```bash
python tests --not_mongodb
python tests --not_slow
python tests --not_mongodb --not_slow
python tests --mongodb
python tests --slow
```

For focused work, running a single pytest file is acceptable:

```bash
python -m pytest tests/test_response.py
```

If dependencies or external services are missing, state exactly what could not be run and why.

## Style And Quality

Panther uses Ruff for formatting and linting.

```bash
ruff format .
ruff check .
ruff check --fix .
```

Rust code under `rust/` uses the standard toolchain:

```bash
cargo fmt --manifest-path rust/Cargo.toml
cargo clippy --manifest-path rust/Cargo.toml --all-targets -- -D warnings
```

Follow the existing style:

- Single quotes for strings unless double quotes are clearer.
- Keep code direct and readable.
- Prefer small functions with obvious control flow.
- Add comments only when they explain non-obvious behavior.
- Avoid broad refactors while fixing narrow issues.

## Architecture Guidelines

- Preserve the lightweight ASGI request path.
- Be careful with global state in `panther.configs.config`; many tests rely on `config.refresh()`.
- Avoid extra per-request allocations in hot paths.
- Avoid repeated JSON serialization or unnecessary body copies.
- Do not block the event loop in async request handling.
- Be cautious when changing routing behavior; many edge cases are covered in `tests/test_routing.py`.
- Be cautious when changing request parsing, multipart handling, response headers, caching, authentication, or database behavior because these affect public APIs.
- Function-based APIs and class-based APIs should stay behaviorally consistent.
- Public behavior changes should include tests and documentation updates.
- Keep the Rust web server opt-in. Uvicorn stays the default, `panther/server.py` must import
  cleanly without the extension, and nothing in `panther/` may require it.
- In `rust/`, keep the one-directional design: Rust publishes connections onto a queue and Python
  drains it. Do not add code paths where Rust calls into the interpreter on its own.

## Documentation Rules

Update `docs/docs/` when a change affects public usage, configuration, CLI behavior, or documented APIs.

Keep docs practical:

- Show minimal working examples.
- Prefer clear explanations over marketing language.
- Mention required optional dependencies when a feature needs them.

## Performance Mindset

Panther aims to be fast. Before adding work to the request path, ask whether it is needed for every request.

Prefer:

- Startup-time validation over per-request validation when possible.
- Cached/precomputed call chains where behavior is static.
- `orjson` for JSON serialization.
- Direct dictionary/list operations over heavy abstractions.
- Lazy parsing when data may not be used.

Avoid:

- Rebuilding middleware chains unnecessarily.
- Serializing the same response body multiple times.
- Reading large request bodies when the endpoint does not need them.
- Hidden side effects during app initialization.
- Global mutable state that prevents multiple apps from coexisting safely.

## Pull Request Checklist

Before finishing a change, verify the relevant subset:

```bash
ruff check .
ruff format .
python tests --not_mongodb --not_slow
```

For database, Redis, WebSocket, or slow-path changes, run the matching full tests when services are available.

A good change should include:

- Focused implementation.
- Tests for new behavior or regressions.
- Documentation updates for public-facing changes.
- A short explanation of any tests that could not be run.

## Agent Safety Rules

- Do not rewrite unrelated code.
- Do not remove compatibility behavior unless explicitly requested.
- Do not change generated docs, benchmark claims, or public APIs casually.
- Do not run destructive git commands.
- Do not commit secrets, local environment files, cache directories, or virtual environments.
- If the working tree already has user changes, preserve them and work around them.
