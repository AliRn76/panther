# Panther Examples

Panther keeps two kinds of examples:

- `canonical/` contains small, focused examples for humans and LLM coding agents. Start there when learning or generating Panther code.
- The top-level examples and `blog/` are scenario examples. They show richer app patterns and may require optional dependencies or create local demo files.

## Quick Start

Run a canonical example:

```bash
panther run examples.canonical.01_single_file:app
```

Run a scenario example:

```bash
panther run examples.streaming_response:app
```

Some examples need optional dependencies:

```bash
pip install "panther[full]"
```

## Scenario Examples

- `streaming_response.py` demonstrates several streaming response patterns.
- `file_upload_example.py` demonstrates multipart uploads, `File`, `Image`, validation, persistence, and PantherDB.
- `broadcast_websocket.py` demonstrates WebSocket broadcast through Panther's connection registry.
- `blog/` is a fuller app with models, serializers, generic APIs, authentication, CORS, Redis, throttling, Docker, and PantherDB.

Generated example data is intentionally written near the example files where practical, so it is easier to find and delete after experimenting.
