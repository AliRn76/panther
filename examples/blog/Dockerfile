# --- Builder ---
FROM python:3.12 AS builder
WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv

# Install uv into system (can be reused)
RUN pip install --no-cache-dir uv

# Copy requirements and install into the venv
COPY requirements.txt .
RUN /usr/local/bin/uv pip install -r requirements.txt --python /opt/venv/bin/python

# --- Final image ---
FROM python:3.12-slim AS production

ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy app source
WORKDIR /app
COPY . /app
