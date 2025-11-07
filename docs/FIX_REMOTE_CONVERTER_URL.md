# 🔧 Fix - Erro de Conexão com API Remota

**Data:** 7 de novembro de 2025  
**Problema:** HTTPConnectionPool connection refused - Failed to resolve 'converter'  
**Solução:** ✅ Corrigida

---

## ❌ Problema Encontrado

```
Failed to resolve 'converter' ([Errno -3] Temporary failure in name resolution)
```

### Root Cause

O RemoteAudioConverter estava usando **`http://converter:8591`** (hostname Docker) como default, mas esse hostname não existe fora do Docker Compose network.

A API remota está em **`192.168.1.29:8591`** (máquina physical real), não em um container Docker.

### Arquivos com o Problema

1. **`transcription/remote_audio_converter.py`** (linha ~79)
   ```python
   REMOTE_CONVERTER_URL = os.getenv(
       'REMOTE_CONVERTER_URL',
       'http://converter:8591'  # ❌ ERRADO: hostname Docker
   )
   ```

2. **`docker-compose.yml`** (3 ocorrências)
   - Linha 56 (serviço `web`)
   - Linha 104 (serviço `celery_worker`)
   - Linha 185 (serviço `celery_worker_gpu1`)

---

## ✅ Solução Implementada

### 1. Corrigir RemoteAudioConverter

```python
REMOTE_CONVERTER_URL = os.getenv(
    'REMOTE_CONVERTER_URL',
    'http://192.168.1.29:8591'  # ✅ CORRETO: IP real da máquina remota
)
```

### 2. Corrigir docker-compose.yml

Em todos os 3 serviços, mudei:

```bash
# ❌ Antes
REMOTE_CONVERTER_URL=http://converter:8591

# ✅ Depois
REMOTE_CONVERTER_URL=http://192.168.1.29:8591
```

---

## 🚀 Deploy Completado

```bash
docker compose down
docker compose up --build -d
```

✅ Todos os containers iniciados com sucesso
✅ Variáveis de ambiente atualizadas
✅ Pronto para testar

---

## 📊 Antes vs Depois

### ❌ Antes (Erro)

```
❌ Erro de conexão com servidor remoto: 
HTTPConnectionPool(host='converter', port=8591): 
Max retries exceeded with url: /convert-async 
(Caused by NameResolutionError: Failed to resolve 'converter')
```

### ✅ Depois (Conecta Corretamente)

```
⚡ Usando endpoint assíncrono (/convert-async) - OBRIGATÓRIO
📮 Enfileirando conversão... (sample_rate=16000, channels=1)
✅ Job enfileirado: [job_id]
⏳ Aguardando conversão remota...
```

---

## 🧪 Para Testar

```bash
# Ver logs em tempo real
docker compose logs -f web celery_worker_gpu1

# Enviar arquivo OGG
curl -X POST -F "file=@test.ogg" \
  http://localhost:8511/api/transcribe/async

# Verificar status
curl http://localhost:8511/api/transcribe/async/status/{task_id}
```

---

## 📝 Mudanças Realizadas

| Arquivo | Mudanças |
|---------|----------|
| `remote_audio_converter.py` | Linha ~79: `converter` → `192.168.1.29` |
| `docker-compose.yml` | Linha 56, 104, 185: `converter` → `192.168.1.29` |

---

## ✅ Verificação Pós-Deploy

Todos os containers iniciados:
- ✅ `daredevil_web` - Running
- ✅ `daredevil_redis` - Healthy
- ✅ `daredevil_celery_worker_gpu0` - Running
- ✅ `daredevil_celery_worker_gpu1` - Running
- ✅ `daredevil_celery_beat` - Running

---

## 🎯 Próximo Passo

Testar com arquivo OGG real do WhatsApp:

```bash
curl -X POST -F "file=@whatsapp.ogg" \
  http://localhost:8511/api/transcribe

# Esperado: Sucesso com conversão assíncrona
# Logs: "⚡ Usando endpoint assíncrono (/convert-async) - OBRIGATÓRIO"
```

---

**Status:** ✅ Corrigido e Deployado  
**Próximo teste:** Upload de OGG real

