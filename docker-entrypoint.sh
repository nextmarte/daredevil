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

# ✅ CRITICAL FIX: Evitar race condition em migrations com múltiplas replicas
# Usar file lock para garantir que apenas uma instância execute migrations
LOCK_FILE="/tmp/daredevil_migrate.lock"
LOCK_TIMEOUT=300  # 5 minutos

echo "Aguardando lock para migrations..."

# Função para adquirir lock com timeout
acquire_lock() {
  local timeout=$1
  local elapsed=0
  
  while [ "$elapsed" -lt "$timeout" ]; do
    # Tentar criar arquivo de lock (atomic operation)
    if mkdir "$LOCK_FILE" 2>/dev/null; then
      # Lock adquirido
      echo "Lock adquirido, executando migrations..."
      return 0
    fi
    
    # Verificar se lock está obsoleto (mais de 10 minutos)
    if [ -d "$LOCK_FILE" ]; then
      lock_age=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
      if [ "$lock_age" -gt 600 ]; then
        echo "Lock obsoleto detectado (idade: ${lock_age}s), removendo..."
        rm -rf "$LOCK_FILE"
        continue
      fi
    fi
    
    # Aguardar antes de tentar novamente
    echo "Lock ocupado, aguardando..."
    sleep 2
    elapsed=$((elapsed + 2))
  done
  
  echo "ERRO: Timeout ao aguardar lock após ${timeout}s"
  return 1
}

# Função para liberar lock
release_lock() {
  if [ -d "$LOCK_FILE" ]; then
    rm -rf "$LOCK_FILE"
    echo "Lock liberado"
  fi
}

# Garantir que lock seja liberado mesmo em caso de erro
trap release_lock EXIT

# Adquirir lock e executar migrations
if acquire_lock "$LOCK_TIMEOUT"; then
  echo "Applying migrations..."
  uv run python manage.py migrate --noinput || true
  uv run python manage.py collectstatic --noinput 2>/dev/null || true
  release_lock
else
  echo "AVISO: Não foi possível adquirir lock, pulando migrations"
  echo "Assumindo que outra instância está executando migrations"
fi

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
