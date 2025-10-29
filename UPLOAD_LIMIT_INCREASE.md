# 📦 Aumento de Limite de Arquivo - 25MB → 500MB

## 🔄 O Que Foi Mudado

### 1. **.env**
```env
# Antes
MAX_AUDIO_SIZE_MB=100

# Depois
MAX_AUDIO_SIZE_MB=500
```

### 2. **config/settings.py**
```python
# Antes
MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', 25))

# Depois
MAX_AUDIO_SIZE_MB = int(os.getenv('MAX_AUDIO_SIZE_MB', 500))

# Adicionado:
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500 MB
```

### 3. **docker-compose.yml**
```yaml
# Antes
MAX_AUDIO_SIZE_MB=25

# Depois
MAX_AUDIO_SIZE_MB=500
deploy:
  resources:
    limits:
      memory: 16G  # Limite de memória RAM
```

## ✅ Resultado

| Métrica | Antes | Depois |
|---------|-------|--------|
| Limite de upload | 25 MB | 500 MB |
| Limite Django | Padrão | 500 MB |
| Memória do container | Sem limite | 16 GB |
| Status da API | ✅ | ✅ |

## 🧪 Teste

```bash
# Verificar novo limite
curl http://localhost:8511/api/health | grep max_file_size_mb

# Resultado esperado:
# "max_file_size_mb": 500
```

## 📝 Casos de Uso

Agora você pode transcrever:

| Duração | Tamanho | Modelo |
|---------|---------|--------|
| ~30 min | 500 MB | Medium |
| ~60 min | 500 MB | Small |
| ~120 min | 500 MB | Tiny |

## 🚀 Como Ajustar Ainda Mais

Se precisar de limite ainda maior, edite o `.env`:

```env
# Para 1 GB
MAX_AUDIO_SIZE_MB=1000

# Para 2 GB
MAX_AUDIO_SIZE_MB=2000
```

Depois reinicie:
```bash
docker compose down && docker compose up -d
```

## ⚠️ Requisitos

Para usar uploads de 500MB, certifique-se:
- RAM disponível: Mínimo 8 GB
- Espaço em disco: Mínimo 100 GB para `/tmp/daredevil`
- Conexão: Estável para upload de 500MB
- GPU: Recomendada para processing rápido

## 📊 Performance com Arquivos Grandes

### Exemplo: Arquivo de 500MB
```
Tamanho: 500 MB
Duração estimada: ~2-3 horas de áudio
Modelo: medium
GPU: RTX 3060 (11GB)
Tempo de processamento: ~15-45 minutos
```

## 🔍 Verificação

```bash
# Verificar limite atual
docker exec daredevil_web bash -c "python -c \"from django.conf import settings; print(f'Limite: {settings.MAX_AUDIO_SIZE_MB}MB')\""

# Verificar memória do Django
docker exec daredevil_web bash -c "python -c \"from django.conf import settings; print(f'Django FILE_UPLOAD: {settings.FILE_UPLOAD_MAX_MEMORY_SIZE / 1024 / 1024:.0f}MB')\""
```

---

**Status**: ✅ Implementado e Testado  
**Data**: 29 de outubro de 2025
