# 🚀 GUIA RÁPIDO - EXECUTAR COM PROTEÇÕES

## ⚡ Passo 1: Instalar Dependência Nova

```bash
cd /home/marcus/projects/daredevil
uv add psutil
uv sync
```

## ⚡ Passo 2: Terminal 1 - Celery Worker

```bash
cd /home/marcus/projects/daredevil
uv run celery -A config worker -l info --concurrency=4
```

**Saída esperada:**
```
 -------------- celery@hostname v5.x.x (sun)
 ---- **** -----
 --- * ***  * -- Linux-5.x
-- * - **** ---
 - ** ---------- [config]
 - ** ----------
 - ** ----------
 - ** ----------
 - ** ----------
 - *** --- * --- Worker Online
```

## ⚡ Passo 3: Terminal 2 - Celery Beat (IMPORTANTE!)

```bash
cd /home/marcus/projects/daredevil
uv run celery -A config beat -l info
```

**Saída esperada:**
```
 -------------- celery beat v5.x.x
 
[2025-11-06 10:30:00,123] INFO: Starting celery beat scheduler
[2025-11-06 10:30:00,456] INFO: Scheduler: <your_scheduler>
[2025-11-06 10:30:00,789] INFO: Timetable: {
  'cleanup-temp-files': <SchedulingError or time spec>,
  'monitor-memory': <SchedulingError or time spec>,
  'unload-gpu-model': <SchedulingError or time spec>,
}
```

## ⚡ Passo 4: Terminal 3 - Django Server

```bash
cd /home/marcus/projects/daredevil
uv run python manage.py runserver
```

**Saída esperada:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## ✅ Testar se Está Funcionando

### 1. Status de Memória
```bash
curl http://localhost:8000/api/memory-status | python -m json.tool
```

**Resposta esperada:**
```json
{
  "memory_usage": {
    "ram_percent": 42.5,
    "ram_available_gb": 9.2,
    "disk_percent": 58.3,
    "disk_free_gb": 150.5
  },
  "temp_dir_size_mb": 125.3,
  "is_critical": false,
  "is_warning": false,
  "thresholds": {
    "ram_critical_percent": 90,
    "ram_warning_percent": 75,
    "disk_critical_percent": 90
  }
}
```

### 2. Status de GPU
```bash
curl http://localhost:8000/api/gpu-status | python -m json.tool
```

### 3. Limpar Temporários Manualmente
```bash
curl -X POST http://localhost:8000/api/cleanup-temp | python -m json.tool
```

### 4. Fazer Upload de Áudio
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@test.mp3" \
  -F "language=pt" | python -m json.tool
```

## 📊 Verificar Logs de Proteção

### Ver logs de memória crítica:
```bash
grep "RAM CRÍTICA\|DISCO CRÍTICO\|ALERTA" <django_logs>
```

### Ver logs de limpeza automática:
```bash
grep "Limpeza de temporários\|arquivos removidos" <celery_logs>
```

### Ver logs de monitoramento:
```bash
grep "Status normal\|AVISO\|CRÍTICO" <celery_beat_logs>
```

## 🔍 Monitorar em Tempo Real

### Terminal 4 - Watch Memory
```bash
watch -n 5 'curl -s http://localhost:8000/api/memory-status | python -m json.tool'
```

### Terminal 5 - Monitor Disk Space
```bash
watch -n 30 'df -h | grep -E "^/dev|tmpfs|Filesystem"'
```

## 🛑 Parar Tudo

```bash
# Terminal 1: CTRL+C (Celery Worker)
# Terminal 2: CTRL+C (Celery Beat)
# Terminal 3: CTRL+C (Django)
```

## ⚠️ Troubleshooting

### "psutil not found"
```bash
uv add psutil
uv sync
```

### "Celery Beat tasks não aparecem"
Verifique se beat está rodando em terminal separado (Terminal 2)

### "Tasks não executam"
1. Verifique se beat está rodando
2. Verifique se worker está rodando
3. Verifique Redis: `redis-cli ping` deve retornar `PONG`

### "Memory status retorna erro"
Pode ser que psutil não está instalado. Execute:
```bash
uv add psutil
```

## 📈 Performance Esperada

| Operação | Tempo | Recurso |
|----------|-------|---------|
| Cleanup task | < 5s | Leve |
| Monitor task | < 2s | Muito leve |
| Unload GPU | 1-3s | Libera 2-10GB VRAM |
| Status endpoint | < 100ms | Muito rápido |

## 🎯 Verificação Final

Tudo funcionando corretamente quando:
- ✅ `curl http://localhost:8000/api/memory-status` retorna JSON
- ✅ Celery worker mostra "Worker Online"
- ✅ Celery beat mostra tasks agendadas
- ✅ Uploads funcionam normalmente
- ✅ Logs mostram limpeza de temporários a cada 30 min

---

**🎉 Pronto! Sistema protegido contra travamentos!**
