# 🚀 Fix: PyTorch com CUDA para GPU Acceleration

## Problema Identificado

❌ **Whisper estava rodando em CPU** (não em GPU), causando transcrição lenta:
- 118 frames/s em CPU
- Esperado: 1000+ frames/s com GPU RTX 3060

**Verificação feita:**
```bash
docker compose exec celery_worker_gpu1 python3 -c "import torch; print(torch.cuda.is_available())"
# Resultado: ModuleNotFoundError: No module named 'torch'
```

**Diagnóstico:** PyTorch não estava instalado no container!

---

## Solução Implementada

### 1. Adicionado PyTorch ao `pyproject.toml`

```toml
dependencies = [
    ...
    "torch>=2.0.0",  # ✅ NOVO: PyTorch com CUDA 12.1
    ...
]
```

### 2. Atualizado `Dockerfile` para instalar PyTorch com CUDA 12.1

```dockerfile
# ✅ NOVO: Instruir UV a usar PyTorch com CUDA 12.1
ENV UV_INDEX_STRATEGY=unsafe-best-match

# ✅ NOVO: Instalar PyTorch com CUDA 12.1 explicitamente
RUN /root/.local/bin/uv pip install --system \
    --index-url https://download.pytorch.org/whl/cu121 \
    'torch>=2.0.0'
```

---

## Como Buildar

Execute este comando para rebuildar com PyTorch CUDA:

```bash
cd /home/marcus/projects/daredevil

# Build completo (reconstrói todas as imagens)
docker compose up -d --build

# Ou apenas o worker GPU
docker compose build --no-cache celery_worker_gpu1
docker compose up -d celery_worker_gpu1
```

**Tempo esperado:** ~5-10 minutos (PyTorch + dependências = ~2GB)

---

## Verificação Após Build

### 1. Verificar se PyTorch está instalado com CUDA:

```bash
docker compose exec celery_worker_gpu1 python3 -c \
  "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

**Saída esperada:**
```
CUDA Available: True
Device: NVIDIA GeForce RTX 3060
```

### 2. Verificar se GPU está sendo usada:

```bash
docker compose exec celery_worker_gpu1 nvidia-smi
```

**Saída esperada (durante transcrição):**
```
| NVIDIA GeForce RTX 3060    | 12288MiB | 2000MiB |    GPU Usage: 100%
```

### 3. Verificar logs de Whisper durante transcrição:

```bash
docker compose logs celery_worker_gpu1 -f | grep -E "GPU|device|cuda"
```

**Saída esperada:**
```
GPU detectada: NVIDIA GeForce RTX 3060 (12.0GB VRAM)
Transcrevendo áudio: ... (idioma: pt, device: cuda)
```

---

## Resultado Esperado Após Fix

### Performance Comparison

| Métrica | Antes (CPU) | Depois (GPU) | Melhoria |
|---------|------------|-------------|---------|
| Frames/s | 118 | 1000+ | 8-10x |
| Transcrição de 1min | ~45s | ~5s | 9x mais rápido |
| Transcrição de 10min | ~450s | ~50s | 9x mais rápido |
| Modelo (medium) | N/A | Usa FP16 | Reduz memória |

### Exemplo de Log Esperado

**Antes (CPU - LENTO):**
```
31%|###       | 21260/69666 [02:56<06:50, 118.01frames/s]
(vai demorar ~9 minutos para 100%)
```

**Depois (GPU - RÁPIDO):**
```
100%|██████████| 69666/69666 [00:35<00:00, 2000+frames/s]
(completa em ~35 segundos)
```

---

## Arquivos Modificados

1. ✅ `pyproject.toml` - Adicionado `torch>=2.0.0`
2. ✅ `Dockerfile` - Adicionadas linhas de instalação de PyTorch com CUDA
3. ✅ `uv.lock` - **Removido** (será regenerado no build)

---

## Próximos Passos

1. ⏳ Executar: `docker compose up -d --build`
2. ⏳ Esperar build completar (~5-10 minutos)
3. ⏳ Testar com: `docker compose exec celery_worker_gpu1 nvidia-smi`
4. ⏳ Submeter um áudio para transcrição e verificar se está rápido
5. ⏳ Ver logs: `docker compose logs celery_worker_gpu1 -f`

---

## Troubleshooting

### Se ainda estiver lento (CPU):

```bash
# 1. Verificar se CUDA está realmente disponível
docker compose exec celery_worker_gpu1 python3 -c "import torch; print(torch.cuda.is_available())"

# 2. Se retornar False, verificar logs do build
docker compose logs web | grep -i "torch\|cuda\|install"

# 3. Se necessário, forçar rebuild limpo
docker compose down
docker system prune -a
docker compose up -d --build
```

### Se PyTorch não instalar:

O problema pode ser:
1. ❌ Imagem base `nvidia/cuda:12.1.0` não tem CUDA runtime
   - **Solução:** Trocar para `nvidia/cuda:12.1.0-runtime-ubuntu22.04`
2. ❌ Índice PyTorch indisponível
   - **Solução:** Usar `--index-url https://download.pytorch.org/whl/cu121`
3. ❌ Memória insuficiente durante build
   - **Solução:** Aumentar Docker memory allocation

---

## Referência

- **PyTorch CUDA Wheels:** https://download.pytorch.org/whl/cu121
- **NVIDIA CUDA 12.1:** https://developer.nvidia.com/cuda-12-1-0-download-archive
- **Whisper Performance:** Com GPU RTX 3060, espera-se 8-10x speedup

---

**Status:** ✅ Implementado
**Próximo:** Executar build e testar performance
