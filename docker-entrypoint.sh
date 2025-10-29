#!/bin/bash
set -e

echo "Checking UV installation..."
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: UV not found! Installing UV..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="/root/.local/bin:$PATH"
fi

echo "UV version: $(uv --version)"

echo "Running uv sync to install Python deps from pyproject.toml (uv-managed)..."
uv sync

echo "Applying migrations and starting server on 0.0.0.0:8000"
uv run python manage.py migrate --noinput || true
uv run python manage.py collectstatic --noinput || true

echo "Starting Django development server..."
exec uv run python manage.py runserver 0.0.0.0:8000
