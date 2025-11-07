#!/bin/bash
# 🔗 Proxy reverso: Redireciona :8591 local para ultron:8591
# Isso permite que host.docker.internal:8591 funcione

# Instalar socat se não tiver (precisa estar no sistema)
if ! command -v socat &> /dev/null; then
    echo "❌ socat não instalado. Peça ao admin: apt-get install socat"
    exit 1
fi

# Matar processos existentes na porta 8591
pkill -f "socat.*8591" 2>/dev/null || true
sleep 1

# Iniciar proxy TCP (SEM sudo, usando porta >= 1024)
echo "🔗 Iniciando proxy: localhost:8591 → ultron.local:8591"
nohup socat TCP-LISTEN:8591,fork,reuseaddr TCP:ultron.local:8591 > /tmp/proxy_8591.log 2>&1 &

# Esperar 1 segundo
sleep 1

# Verificar se está rodando
if pgrep -f "socat.*8591" > /dev/null; then
    echo "✅ Proxy ativo! Testando..."
    curl -s -m 2 http://localhost:8591/health 2>&1 | head -2
    echo ""
    echo "✅ Container agora pode acessar host.docker.internal:8591"
    echo "📋 PID: $(pgrep -f 'socat.*8591')"
else
    echo "❌ Falha ao iniciar proxy"
    cat /tmp/proxy_8591.log
    exit 1
fi
