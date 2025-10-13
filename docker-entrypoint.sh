#!/bin/sh
set -e

# Instala ffmpeg no ambiente alpine se faltar
if command -v apk >/dev/null 2>&1; then
  echo "Installing ffmpeg via apk..."
  apk update || true
  apk add --no-cache ffmpeg bash build-base
fi

echo "Running uv sync to install Python deps from pyproject.toml (uv-managed)..."
if command -v uv >/dev/null 2>&1; then
  uv sync || true
fi

echo "Applying migrations and starting server on 0.0.0.0:8511"
python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true

exec uv run python manage.py runserver 0.0.0.0:8511
