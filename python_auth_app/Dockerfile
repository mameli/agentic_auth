# Stage 1: Build stage with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime stage
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY src/ ./src/
COPY templates/ ./templates/

# Set environment to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=5555
# Run the application
ENV PORT=5555
CMD ["sh", "-c", "python -m fastapi run src/python_auth_app/main.py --host 0.0.0.0 --port ${PORT}"]
