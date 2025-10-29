#!/bin/bash
# Script de conveniência para verificar status da GPU no Daredevil

echo "🔍 Verificando configuração de GPU..."
echo ""

# Verificar se o container está rodando
if ! docker ps | grep -q daredevil_web; then
    echo "❌ Container daredevil_web não está rodando"
    echo "Execute: docker compose up -d"
    exit 1
fi

echo "✓ Container está rodando"
echo ""

# Verificar GPU via API
echo "📡 Verificando GPU via API..."
response=$(curl -s http://localhost:8511/api/gpu-status 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "❌ Não foi possível conectar à API"
    echo "Verifique se o servidor está rodando: docker compose logs web"
fi

echo ""
echo "🖥️  Verificando nvidia-smi no container..."
docker exec daredevil_web nvidia-smi 2>/dev/null || echo "❌ nvidia-smi não disponível"

echo ""
echo "🐍 Verificando PyTorch CUDA..."
docker exec daredevil_web uv run python -c "import torch; print(f'✓ PyTorch version: {torch.__version__}'); print(f'✓ CUDA available: {torch.cuda.is_available()}'); print(f'✓ CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'✓ Device count: {torch.cuda.device_count() if torch.cuda.is_available() else 0}')" 2>/dev/null

echo ""
echo "📊 Logs recentes do container:"
docker logs --tail 20 daredevil_web 2>/dev/null

echo ""
echo "✅ Verificação concluída!"
