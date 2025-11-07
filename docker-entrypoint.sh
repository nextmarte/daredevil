#!/bin/bash
set -e

# 🔗 Garantir resolução DNS de host.docker.internal
# Necessário quando usando network_mode: host (não herda extra_hosts)
if ! grep -q "host.docker.internal" /etc/hosts 2>/dev/null; then
  # Detecta IP do gateway (host)
  GATEWAY_IP=$(ip route | grep default | awk '{print $3}')
  if [ -n "$GATEWAY_IP" ]; then
    echo "$GATEWAY_IP    host.docker.internal" >> /etc/hosts || true
  fi
fi

echo "Checking UV installation..."
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: UV not found! Installing UV..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="/root/.local/bin:$PATH"
fi

echo "UV version: $(uv --version)"

echo "Running uv sync to install Python deps from pyproject.toml (uv-managed)..."
uv sync

# Função para executar migrations com lock para evitar race condition
# quando múltiplas réplicas tentam migrar ao mesmo tempo
run_migrations_with_lock() {
  local lockfile="/tmp/daredevil-migration.lock"
  local lockfd=200
  
  # Criar diretório se não existir
  mkdir -p /tmp
  
  # Tentar adquirir lock exclusivo com timeout
  exec 200>"$lockfile"
  
  echo "Aguardando lock para executar migrations..."
  if flock -w 300 200; then
    echo "Lock adquirido, executando migrations..."
    uv run python manage.py migrate --noinput || true
    uv run python manage.py collectstatic --noinput 2>/dev/null || true
    echo "Migrations concluídas, liberando lock..."
    flock -u 200
  else
    echo "AVISO: Timeout ao aguardar lock de migrations (300s). Continuando mesmo assim..."
    # Tentar executar migrations mesmo sem lock (melhor do que não executar)
    uv run python manage.py migrate --noinput || true
    uv run python manage.py collectstatic --noinput 2>/dev/null || true
  fi
  
  exec 200>&-  # Fechar file descriptor
}

echo "Applying migrations with lock..."
run_migrations_with_lock

# Verificar se há comando passado como argumento (para Celery/Beat)
if [ $# -gt 0 ]; then
  echo "Executando comando passado como argumento: $@"
  exec uv run "$@"
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
