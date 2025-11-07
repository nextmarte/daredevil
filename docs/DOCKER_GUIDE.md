# 🐳 EXECUTAR COM DOCKER (COM PROTEÇÕES)

## 📋 O que foi Atualizado

### ✅ `docker-compose.yml` - AGORA COM CELERY BEAT

**Novos serviços:**
- ✅ `redis` - Broker de mensagens (já existia)
- ✅ `web` - Django server (atualizado com novas variáveis)
- ✅ `celery_worker` - Worker async (atualizado)
- ✅ `celery_beat` - **NOVO! Tasks agendadas de proteção** ⭐

**Novas variáveis de ambiente:**
```yaml
- MEMORY_CRITICAL_THRESHOLD_PERCENT=90
- MEMORY_WARNING_THRESHOLD_PERCENT=75
- DISK_CRITICAL_THRESHOLD_PERCENT=90
- TEMP_DIR_MAX_SIZE_MB=5000
- MAX_CONCURRENT_TRANSCRIPTIONS=4
```

### ✅ `Dockerfile` - Sem mudanças necessárias
Já está correto com:
- `nvidia/cuda:12.1.0-base-ubuntu22.04`
- `ffmpeg` instalado
- `UV` instalado
- `python3.12`

---

## 🚀 Como Executar com Docker

### Opção 1: Docker Compose Completo (Recomendado)

```bash
cd /home/marcus/projects/daredevil

# Construir imagem
docker-compose build

# Iniciar todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps
```

**Saída esperada:**
```
NAME                      COMMAND                  STATUS
daredevil_redis           redis-server             Up
daredevil_web             /app/docker-entrypoint  Up
daredevil_celery_worker   celery -A config worker Up
daredevil_celery_beat     celery -A config beat   Up ⭐ CRÍTICO
```

### Opção 2: Parar Todos os Serviços

```bash
docker-compose down
```

### Opção 3: Remover Volumes (Limpar Dados)

```bash
docker-compose down -v
```

---

## ✅ Testar se Está Funcionando

### 1. Verificar Logs de Inicialização

```bash
# Logs gerais
docker-compose logs -f

# Apenas Django
docker-compose logs -f web

# Apenas Worker
docker-compose logs -f celery_worker

# Apenas Beat (IMPORTANTE!)
docker-compose logs -f celery_beat
```

**Logs esperados do Beat:**
```
celery_beat  | [2025-11-06 10:30:00,123] INFO: Starting celery beat scheduler
celery_beat  | [2025-11-06 10:30:00,456] INFO: Scheduler started
celery_beat  | [2025-11-06 10:30:00,789] INFO: Tasks scheduled: cleanup-temp-files, monitor-memory, unload-gpu-model
```

### 2. Testar Endpoint de Memória

```bash
curl http://localhost:8511/api/memory-status | python -m json.tool
```

**Resposta esperada:**
```json
{
  "memory_usage": {
    "ram_percent": 42.5,
    "ram_available_gb": 9.2,
    "disk_percent": 58.3
  },
  "is_critical": false,
  "is_warning": false
}
```

### 3. Limpar Temporários Manualmente

```bash
curl -X POST http://localhost:8511/api/cleanup-temp
```

### 4. Fazer Upload de Teste

```bash
# Crie um arquivo de teste
echo "teste" > test.txt

curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@test.txt" \
  -F "language=pt"
```

### 5. Verificar Tasks Agendadas

```bash
# Entrar no container do Beat
docker exec -it daredevil_celery_beat bash

# Dentro do container, verificar logs
tail -f /var/log/celery/beat.log
```

---

## 🔍 Monitorar Tarefas Automáticas

### Verificar se Cleanup rodou

```bash
docker-compose logs celery_beat | grep -i "cleanup-temp"
```

**Esperado a cada 30 minutos:**
```
celery_beat: Task 'transcription.cleanup_temp_files_task' sent to worker
```

### Verificar se Monitoramento rodou

```bash
docker-compose logs celery_beat | grep -i "monitor-memory"
```

**Esperado a cada 5 minutos:**
```
celery_beat: Task 'transcription.monitor_memory_task' sent to worker
```

### Verificar se GPU foi descarregada

```bash
docker-compose logs celery_beat | grep -i "unload-gpu"
```

**Esperado a cada 1 hora:**
```
celery_beat: Task 'transcription.unload_gpu_model_task' sent to worker
```

---

## 📊 Monitoramento em Tempo Real

### Terminal 1: Acompanhar Logs

```bash
docker-compose logs -f
```

### Terminal 2: Monitorar Recursos do Container

```bash
docker stats --no-stream daredevil_web daredevil_celery_worker
```

**Saída esperada:**
```
CONTAINER ID    NAME                  CPU %    MEM USAGE / LIMIT
abc123          daredevil_web         2.5%     2.4GB / 16GB
def456          daredevil_celery_wor  1.2%     1.8GB / 16GB
```

### Terminal 3: Acompanhar Espaço em Disco

```bash
watch -n 5 'du -sh /tmp/daredevil && df -h | grep -E "^/dev|tmpfs"'
```

---

## ⚙️ Configurações Avançadas

### Alterar Limite de Memória

Edite `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 32G  # Aumentar de 16G para 32G
```

### Alterar Concorrência de Worker

Edite `docker-compose.yml`:
```yaml
celery_worker:
  command: celery -A config worker --concurrency=8  # Aumentar de 2 para 8
```

### Alterar Variáveis de Proteção

Edite `docker-compose.yml`:
```yaml
environment:
  - MEMORY_CRITICAL_THRESHOLD_PERCENT=85  # Mais agressivo (85% em vez de 90%)
  - TEMP_DIR_MAX_SIZE_MB=10000            # Aumentar limite de /tmp
```

### Usar GPU Específica

Edite `docker-compose.yml`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0']  # Apenas GPU 0
          capabilities: [gpu]
```

---

## 🚨 Troubleshooting

### "Docker Compose não encontra nvidia"

Verifique se NVIDIA Container Runtime está instalado:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

Se não funcionar:
```bash
# Instalar NVIDIA Container Runtime
sudo apt-get install -y nvidia-container-runtime
sudo systemctl restart docker
```

### "Celery Beat não está rodando"

Verifique se container `daredevil_celery_beat` existe:
```bash
docker ps | grep celery_beat
```

Se não aparecer, inicie manualmente:
```bash
docker-compose up celery_beat -d
```

### "Memory check retorna erro"

```bash
# Verificar se psutil está instalado no container
docker exec daredevil_web python -c "import psutil; print('OK')"
```

Se não funcionar, reconstrua a imagem:
```bash
docker-compose build --no-cache web
docker-compose up -d
```

### "Tasks não executam"

1. Verifique se Beat está rodando:
```bash
docker-compose logs celery_beat
```

2. Verifique se Worker está rodando:
```bash
docker-compose logs celery_worker
```

3. Verifique se Redis está rodando:
```bash
docker-compose logs redis
```

4. Se nada resolver, reinicie tudo:
```bash
docker-compose down
docker-compose up -d
```

---

## 📈 Performance Esperada em Docker

| Componente | Memória | CPU | Tempo Boot |
|-----------|---------|-----|-----------|
| Redis | ~50MB | <1% | <2s |
| Django Web | ~800MB | 1-3% | ~30s |
| Celery Worker | ~2GB | <1% (idle) | ~30s |
| Celery Beat | ~600MB | <1% | ~20s |
| **Total** | ~3.5GB | 2-5% | ~60s |

---

## ✅ Checklist Final

- [ ] Docker Compose atualizado
- [ ] `docker-compose build` executa sem erros
- [ ] `docker-compose up -d` inicia 4 containers
- [ ] `docker-compose ps` mostra todos os containers "Up"
- [ ] `curl http://localhost:8511/api/memory-status` retorna JSON
- [ ] Logs mostram tasks agendadas
- [ ] Beat está rodando (verificar `docker-compose logs celery_beat`)
- [ ] Worker está rodando (verificar `docker-compose logs celery_worker`)
- [ ] Transcrição funciona (`curl -X POST http://localhost:8511/api/transcribe`)

---

## 🎯 Benefícios do Docker

✅ **Isolamento completo** - Não afeta sistema host  
✅ **Reprodutível** - Mesmo ambiente em dev/prod  
✅ **Escalável** - Fácil adicionar mais workers  
✅ **GPU suportada** - Automático com NVIDIA Runtime  
✅ **Proteções ativas** - Beat roda automaticamente  

---

## 📚 Referências

- Docker Compose: https://docs.docker.com/compose/
- NVIDIA Container Runtime: https://github.com/NVIDIA/nvidia-docker
- Celery Beat: https://docs.celeryproject.io/en/stable/userguide/periodic-tasks.html

---

**🎉 Docker atualizado com proteções contra travamento!**
