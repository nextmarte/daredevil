# 🔍 DIAGNÓSTICO - Problema de Conectividade da Rede Docker

## Problema Identificado

✅ **De fora do container** (seu host):
```bash
curl http://ultron.local:8591/health  # FUNCIONA ✅
```

❌ **De dentro do container:**
```bash
docker exec daredevil_web curl http://ultron.local:8591/health  # FALHA ❌
```

## Diagnóstico Técnico

### 1️⃣ DNS (Funciona)
```bash
# Dentro do container:
curl http://ultron.local:8591/health
# → Consegue resolver ultron.local → 192.168.1.29
# → MAS não consegue conectar na porta TCP
```

### 2️⃣ TCP/IP (Falha)
```bash
# Teste de conectividade TCP dentro do container:
(exec 3<>/dev/tcp/ultron.local/8591)
# → TIMEOUT (porta não alcançável)
```

### 3️⃣ Razão
A rede Docker **isolada** não consegue alcançar `192.168.1.29` porque:
- Container conecta via bridge do Docker (172.17.0.x)
- Seu host tem IP 192.168.1.x
- Máquina remota (ultron) também tem IP 192.168.1.x
- **Docker container não consegue rotear pacotes para sua rede local**

## Solução

### Opção 1: Usar `host.docker.internal` (RECOMENDADO)

Se a API remota está **na mesma máquina** que o Daredevil:

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - REMOTE_CONVERTER_URL=http://host.docker.internal:8591
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**Teste:**
```bash
docker exec daredevil_web curl http://host.docker.internal:8591/health
```

### Opção 2: Expor a API com `0.0.0.0` no host

Se a API remota está em outra máquina, ela precisa escutar em `0.0.0.0:8591` (não apenas `127.0.0.1:8591`).

### Opção 3: Network Host (Menos seguro)

```yaml
# docker-compose.yml
services:
  web:
    network_mode: "host"  # ⚠️ Expõe a máquina toda
```

### Opção 4: Passar IP real do host

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - REMOTE_CONVERTER_URL=http://192.168.1.69:8591  # IP do seu host (skynet01)
    extra_hosts:
      - "ultron.local:192.168.1.69"  # Se API está rodando no host
```

## Onde está a API remota?

Você precisa confirmar:

**1️⃣ Está em `ultron` (máquina remota 192.168.1.29)?**
```bash
# No seu host:
ssh user@192.168.1.29
docker ps  # ou ps aux | grep 8591
```

**2️⃣ Está no seu `host` (skynet01 192.168.1.69)?**
```bash
ps aux | grep 8591  # Processo rodando direto no host
# ou
docker ps | grep converter  # Container rodando localmente
```

**3️⃣ Qual é o IP/nome correto?**
```bash
# Descobrir IPs da máquina com a API:
hostname -I
hostname
```

## Status Atual

### ✅ Verificado
- DNS resolve `ultron.local` → `192.168.1.29` ✅
- Container tem `extra_hosts` configurado ✅
- API remota está respondendo em `ultron.local:8591` ✅

### ❌ Problema
- Container **não consegue alcançar TCP** em `192.168.1.29:8591` ❌
- Possível causa: Máquina não está acessível da rede Docker ❌

## Próximas Ações

1. **Confirmar localização da API remota**
   ```bash
   # Dentro do container, testar diferentes IPs:
   docker exec daredevil_web curl http://172.17.0.1:8591/health  # Gateway Docker
   docker exec daredevil_web curl http://127.0.0.1:8591/health   # Localhost
   docker exec daredevil_web curl http://host.docker.internal:8591/health  # Host especial
   ```

2. **Verificar se API escuta em `0.0.0.0`**
   ```bash
   netstat -tlnp | grep 8591  # Ver em qual interface escuta
   ```

3. **Permitir acesso pela rede**
   - Firewall: `sudo ufw allow 8591/tcp`
   - Roteamento: Verificar se IP local consegue alcançar remoto

4. **Atualizar configuração docker-compose.yml**
   - Se em host: usar `host.docker.internal`
   - Se em outra máquina: usar IP real e verificar firewall

## Teste Rápido

```bash
# Teste do seu host (funciona):
curl http://ultron.local:8591/health
# → {"status":"ok",...}

# Teste de dentro do container (falha):
docker exec daredevil_web curl http://ultron.local:8591/health
# → curl: (7) Failed to connect

# Teste com host.docker.internal:
docker exec daredevil_web curl http://host.docker.internal:8591/health
# → Se funcionar, significa API está no host local!
```

---

**Status:** 🔴 **BLOQUEADO - Aguardando confirmação da localização da API**

Próximo passo: Confirmar onde exatamente a API remota está rodando!
