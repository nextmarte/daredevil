# 📊 Resumo de Mudanças - Performance GPU

## 🎯 O que foi descoberto

Transcrição estava **lenta** (118 frames/s) porque:
- ❌ PyTorch **não estava instalado** no container
- ❌ Whisper rodava em **CPU em vez de GPU**
- ❌ RTX 3060 disponível mas **não sendo usada**

---

## ✅ O que foi corrigido

### 1️⃣ `pyproject.toml`
```diff
dependencies = [
    ...
+   "torch>=2.0.0",  # ✅ PyTorch com CUDA 12.1
    "pydub>=0.25.1",
    ...
]
```

### 2️⃣ `Dockerfile`
```diff
# Adicionar UV ao PATH permanentemente
ENV PATH="/root/.local/bin:$PATH"

+# ✅ Instruir UV a usar PyTorch com CUDA 12.1
+ENV UV_INDEX_STRATEGY=unsafe-best-match

# Copiar arquivos do projeto
COPY pyproject.toml uv.lock* /app/
COPY . /app/

+# ✅ Instalar PyTorch com CUDA 12.1 explicitamente
+RUN /root/.local/bin/uv pip install --system \
+    --index-url https://download.pytorch.org/whl/cu121 \
+    'torch>=2.0.0'

# Tornar os scripts executáveis
RUN chmod +x /app/docker-entrypoint.sh /app/scripts/gpu_worker.sh
```

### 3️⃣ `uv.lock`
```diff
- uv.lock (arquivo removido, será regenerado)
```

---

## 🚀 Como Executar

```bash
cd /home/marcus/projects/daredevil
docker compose up -d --build
```

**Tempo:** ~5-10 minutos (download + compilação de PyTorch)

---

## ✔️ Como Verificar

Após o build completar:

```bash
# Verificar se CUDA está disponível
docker compose exec celery_worker_gpu1 python3 -c \
  "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"

# Esperado: CUDA: True, GPU: NVIDIA GeForce RTX 3060
```

---

## 📈 Performance Esperada

| Item | Antes | Depois | Ganho |
|------|-------|--------|-------|
| Frames/s | 118 | 1000+ | **8-10x** |
| 1 minuto áudio | 45s | 5s | **9x** |
| 10 minutos áudio | 450s (7:30) | 50s | **9x** |

---

## 📚 Documentação

Ver arquivo completo em: `docs/GPU_CUDA_FIX.md`

---

**Status:** ✅ Pronto para build
**Próximo:** `docker compose up -d --build`
