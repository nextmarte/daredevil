#!/bin/bash

###############################################################################
# 🧪 Script de Teste - Conectividade com Conversor Remoto
# 
# Testa se a API de conversão remota está acessível e funcionando
# Uso: bash check_remote_converter.sh
###############################################################################

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🧪 TESTE DE CONECTIVIDADE - CONVERSOR REMOTO DE ÁUDIO               ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuração
REMOTE_URL="${REMOTE_CONVERTER_URL:-http://192.168.1.29:8591}"
TIMEOUT=5

echo -e "${BLUE}📍 URL do Conversor Remoto:${NC} $REMOTE_URL"
echo ""

# ============================================================================
# TESTE 1: Health Check
# ============================================================================
echo -e "${BLUE}1️⃣  Health Check...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if response=$(curl -s -m $TIMEOUT "$REMOTE_URL/health" 2>/dev/null); then
    if [ ! -z "$response" ]; then
        echo -e "${GREEN}✅ Serviço remoto ACESSÍVEL${NC}"
        echo "Resposta:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo -e "${RED}❌ Resposta vazia${NC}"
    fi
else
    echo -e "${RED}❌ Serviço remoto NÃO ACESSÍVEL${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Possíveis causas:${NC}"
    echo "   • Máquina remota offline"
    echo "   • Porta 8591 bloqueada no firewall"
    echo "   • Serviço não rodando na máquina remota"
    echo "   • IP/URL incorreto"
    echo ""
    echo -e "${YELLOW}💡 Solução:${NC}"
    echo "   1. Verificar se serviço remoto está rodando:"
    echo "      docker-compose ps  # Na máquina remota"
    echo ""
    echo "   2. Verificar conectividade:"
    echo "      ping 192.168.1.x"
    echo ""
    echo "   3. Configurar URL correta:"
    echo "      export REMOTE_CONVERTER_URL=http://192.168.1.x:8591"
    echo ""
fi

echo ""

# ============================================================================
# TESTE 2: Status
# ============================================================================
echo -e "${BLUE}2️⃣  Status do Serviço...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if response=$(curl -s -m $TIMEOUT "$REMOTE_URL/status" 2>/dev/null); then
    if [ ! -z "$response" ]; then
        echo -e "${GREEN}✅ Status obtido com sucesso${NC}"
        echo "Resposta:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo -e "${YELLOW}⚠️  Resposta vazia${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Não foi possível obter status${NC}"
fi

echo ""

# ============================================================================
# TESTE 3: Teste de Conversão (opcional)
# ============================================================================
echo -e "${BLUE}3️⃣  Teste de Conversão (requer arquivo)...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "test.mp3" ] || [ -f "test.wav" ]; then
    TEST_FILE=$(ls test.mp3 test.wav 2>/dev/null | head -1)
    echo "Arquivo de teste encontrado: $TEST_FILE"
    echo ""
    echo "Enviando para conversão..."
    
    if response=$(curl -s -m $TIMEOUT -X POST \
        -F "file=@$TEST_FILE" \
        "$REMOTE_URL/convert" -o "/tmp/test_output.wav" 2>/dev/null); then
        
        if [ -f "/tmp/test_output.wav" ]; then
            SIZE=$(ls -lh /tmp/test_output.wav | awk '{print $5}')
            echo -e "${GREEN}✅ Conversão bem-sucedida!${NC}"
            echo "   Arquivo convertido: /tmp/test_output.wav ($SIZE)"
        else
            echo -e "${RED}❌ Arquivo não foi criado${NC}"
        fi
    else
        echo -e "${RED}❌ Erro na conversão${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  Nenhum arquivo de teste encontrado${NC}"
    echo "   Para testar conversão, crie um arquivo test.mp3 ou test.wav"
fi

echo ""

# ============================================================================
# RESUMO
# ============================================================================
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  📊 RESUMO DO TESTE                                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

if response=$(curl -s -m $TIMEOUT "$REMOTE_URL/health" 2>/dev/null); then
    if [ ! -z "$response" ]; then
        echo -e "${GREEN}✅ Serviço remoto está ACESSÍVEL e FUNCIONANDO${NC}"
        echo ""
        echo "Próximas ações:"
        echo "  1. Configurar variáveis de ambiente no Daredevil"
        echo "  2. Executar testes de integração:"
        echo "     python test_remote_converter_integration.py"
        echo "  3. Deploy do Daredevil com Docker Compose"
        echo "  4. Fazer upload de arquivo para testar"
    else
        echo -e "${RED}❌ Serviço remoto não está respondendo${NC}"
    fi
else
    echo -e "${RED}❌ Não foi possível conectar ao serviço remoto${NC}"
    echo ""
    echo "📋 Checklist:"
    echo "  [ ] Máquina remota ligada e conectada"
    echo "  [ ] Serviço remoto rodando (docker-compose up -d)"
    echo "  [ ] Firewall permite porta 8591"
    echo "  [ ] URL/IP configurado corretamente"
    echo "  [ ] Conexão de rede funcional"
    echo ""
    echo "🔧 Para debugar:"
    echo "  1. SSH na máquina remota:"
    echo "     ssh user@192.168.1.x"
    echo ""
    echo "  2. Verificar se Docker está rodando:"
    echo "     docker-compose ps"
    echo ""
    echo "  3. Ver logs do serviço:"
    echo "     docker-compose logs -f app"
    echo ""
    echo "  4. Testar localmente na máquina remota:"
    echo "     curl http://localhost:8591/health"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
