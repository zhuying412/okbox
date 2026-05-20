FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "okbox.main:app", "--host", "0.0.0.0", "--port", "8000"]
