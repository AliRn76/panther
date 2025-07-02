# Deploying Panther Applications

Panther is an ASGI-compatible web framework, which means you can deploy your Panther app using any ASGI server, such as **Uvicorn**, **Granian**, **Daphne**, or others. This guide covers best practices and options for deploying your Panther application in production.

---

## 1. Production-Ready ASGI Servers

While Panther comes with a convenient CLI, you are not limited to it. You can use any ASGI server to run your app:

- **Uvicorn** (default, recommended)
- **Granian**
- **Daphne**
- **Hypercorn**
- Any other ASGI-compliant server

### Example: Using Uvicorn Directly

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

- `main:app` refers to your application instance (e.g., `app = Panther(...)` in `main.py`).
- Adjust `--workers` for your server's CPU count.

### Example: Using Gunicorn with Uvicorn Workers

For robust process management and multiple workers:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

---

## 2. Using the Panther CLI

Panther provides a built-in CLI for development and deployment. The command:

```bash
panther run main:app --reload
```

is **an alias for running Uvicorn** with your Panther app. You can use all Uvicorn options with this command.

- `--reload` is for development (auto-reloads on code changes).
- Omit `--reload` for production.

**Note:** For advanced deployment, prefer running Uvicorn (or another ASGI server) directly, as shown above.

---

## 3. Environment Variables & Configuration

- Set environment variables (e.g., `PORT`, `HOST`, `DATABASE_URL`) as needed for your deployment environment.
- Use a process manager (e.g., **systemd**, **supervisor**, **pm2**, or **Docker** (recomended)) to keep your app running and restart on failure.

---

## 4. Static Files & Reverse Proxy

Panther does not serve static files in production. Use a reverse proxy (like **Nginx** or **Caddy**) to:

- Serve static files (JS, CSS, images)
- Forward requests to your ASGI server (Uvicorn, etc.)
- Handle HTTPS/SSL termination

**Example Nginx config:**
```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 5. WebSocket & Multiple Workers

If your app uses WebSockets and you want to run multiple workers, configure **Redis** for pub/sub support (see [Redis Integration](redis.md)).  
Alternatively, use the `--preload` flag with Gunicorn for basic multi-worker support (see [WebSocket docs](websocket.md)).

---

## 6. Example: Docker Deployment

Panther can be efficiently containerized using a multi-stage Docker build and the [uv](https://github.com/astral-sh/uv) package manager, which is significantly faster and more reliable than pip. This approach results in smaller, more secure images and faster build times.

### Advantages of Multi-Stage & uv
- **Smaller final image size**: Only production dependencies and app code are included.
- **Faster dependency installation**: `uv` is much faster than `pip` and supports modern lockfiles.
- **Better security**: Build tools and caches are left behind in the builder stage.
- **Cleaner builds**: No unnecessary files in the final image.

### Example Multi-Stage Dockerfile with uv

```dockerfile
FROM python:3.12 AS builder
WORKDIR /app
RUN python -m venv /opt/venv
RUN pip install --no-cache-dir uv
COPY requirements.txt .
RUN /opt/venv/bin/uv pip install -r requirements.txt --system

FROM python:3.12-slim AS production
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
