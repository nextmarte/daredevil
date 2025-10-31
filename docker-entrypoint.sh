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

echo "Applying migrations..."
uv run python manage.py migrate --noinput || true
uv run python manage.py collectstatic --noinput 2>/dev/null || true

# Verificar se está em modo desenvolvimento ou produção
if [ "$DEBUG" = "1" ]; then
  echo "Starting Django development server on 0.0.0.0:8000..."
  exec uv run python manage.py runserver 0.0.0.0:8000
else
  echo "Starting Gunicorn server on 0.0.0.0:8000..."
  # Instalar gunicorn se não estiver
  uv pip install gunicorn 2>&1 || uv add gunicorn
  
  # Iniciar Gunicorn com workers otimizados
  exec uv run gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    config.wsgi
fi
