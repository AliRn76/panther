# Panther Blog Example

A fuller Panther application with posts, comments, authentication, serializers, generic APIs, CORS, throttling, Redis configuration, Docker, and PantherDB.

Post has `title` and `content`. Comment belongs to a post. Anonymous users can view posts. Only authenticated users can create comments.

## Run Locally

From the `examples/blog` directory:

```bash
pip install -r requirements.txt
panther run main:app
```

This example intentionally uses optional Panther integrations: Redis, JWT authentication, CORS middleware, monitoring middleware, and PantherDB. Use the local `requirements.txt` before running it directly.

Or run with Docker Compose:

```bash
docker compose up --build
```

The PantherDB demo database is created at `examples/blog/database.pdb`.
