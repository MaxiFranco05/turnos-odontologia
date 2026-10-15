# Dockerfile - FastAPI application container (lightweight)
# Stage 1: Build dependencies
FROM python:3.11-slim-bookworm AS builder

# Install system dependencies required for PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -r pyproject.toml 2>/dev/null || true

# Copy application code
COPY app/ ./app/

# Stage 2: Runtime (final image)
FROM python:3.11-slim-bookworm

# Install minimal system deps for psycopg3
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root)
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages ./usr/local/lib/python3.11/site-packages

# Copy application code
COPY app/ ./app/

# Expose FastAPI port
EXPOSE 8000

# Set non-root user
USER appuser

# Command to run the application
CMD ["python", "-m", "app.core.main"]