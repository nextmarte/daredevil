# Resumo das Mudanças para Suporte a GPU

## 📋 Arquivos Modificados

### 1. **docker-compose.yml**
✅ Adicionada configuração de GPU NVIDIA:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### 2. **Dockerfile**
✅ Alterada imagem base de `python:3.12-slim` para `nvidia/cuda:12.1.0-base-ubuntu22.04`
✅ Adicionada instalação do Python 3.12 manualmente (via PPA deadsnakes)
✅ Configuração automática de timezone (evita prompts interativos)
✅ Instalação de `python3.12-venv` (distutils foi removido no Python 3.12+)
✅ Configuração correta do PATH para UV
✅ Uso do ENTRYPOINT para executar o docker-entrypoint.sh

### 3. **docker-entrypoint.sh**
✅ Correção CRÍTICA: Todos os comandos Python agora usam `uv run`
```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

### 4. **transcription/services.py**
✅ Importação do PyTorch: `import torch`
✅ Novo método `get_device()` para detectar GPU
✅ Carregamento do modelo Whisper no dispositivo correto (GPU/CPU)
✅ Logs de informações da GPU (nome, memória, etc.)

### 5. **transcription/api.py**
✅ Importação do PyTorch: `import torch`
✅ Novo endpoint `/api/gpu-status` para verificar status da GPU
```bash
GET /api/gpu-status
```

### 6. **Novos Arquivos Criados**

#### GPU_SETUP.md
- Guia completo de instalação do NVIDIA Container Toolkit
- Instruções para Ubuntu, Fedora, RHEL
- Configurações avançadas de GPU
- Troubleshooting

#### test_gpu.py
- Script de teste para verificar configuração de GPU
- Testa nvidia-smi, PyTorch, Whisper
- Mostra informações de memória e capacidade

## 🚀 Como Usar

### 1. Pré-requisitos
```bash
# Instalar NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 2. Build e Start
```bash
# Build com GPU
docker compose build

# Iniciar container
docker compose up -d

# Verificar logs
docker compose logs -f
```

### 3. Testar GPU
```bash
# Verificar se GPU está disponível
docker exec daredevil_web uv run python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Testar com script completo
docker exec daredevil_web uv run python test_gpu.py

# Verificar API
curl http://localhost:8511/api/gpu-status
```

## 📊 Performance Esperada

### Com GPU (NVIDIA RTX 3060+)
- Whisper base: ~5-10x mais rápido
- Whisper small: ~4-8x mais rápido
- Whisper medium: ~3-6x mais rápido
- Whisper large: ~2-4x mais rápido

### Exemplo Real
- Áudio de 5 minutos com modelo medium:
  - **CPU**: ~45-60 segundos
  - **GPU**: ~8-15 segundos

## 🔧 Configurações Importantes

### Variáveis de Ambiente (docker-compose.yml)
```yaml
environment:
  - WHISPER_MODEL=medium          # Use large com GPU
  - CUDA_VISIBLE_DEVICES=0        # Opcional: especificar GPU
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Otimizar memória
```

### Usar GPU Específica
Se você tem múltiplas GPUs:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0']  # Usar apenas GPU 0
          capabilities: [gpu]
```

## 🎯 Endpoints da API

### Verificar GPU
```bash
# Status completo da GPU
GET /api/gpu-status

# Exemplo de resposta
{
  "gpu_available": true,
  "device": "cuda",
  "gpu_count": 1,
  "gpus": [{
    "id": 0,
    "name": "NVIDIA GeForce RTX 3060",
    "memory_allocated_gb": 2.5,
    "memory_total_gb": 12.0,
    "memory_free_gb": 9.5
  }]
}
```

### Health Check
```bash
GET /api/health
```

## ⚠️ Notas Importantes

1. **UV no Docker**: SEMPRE usar `uv run python` dentro do container
2. **Memória GPU**: Modelo large precisa de ~10GB VRAM
3. **Fallback**: Se GPU não disponível, usa CPU automaticamente
4. **Logs**: O sistema faz log da GPU detectada no startup

## 🐛 Troubleshooting

### GPU não detectada
```bash
# Verificar nvidia-smi
docker exec daredevil_web nvidia-smi

# Verificar PyTorch
docker exec daredevil_web uv run python -c "import torch; print(torch.cuda.is_available())"
```

### CUDA out of memory
- Usar modelo menor (base ou small)
- Limitar device_ids para usar menos GPUs
- Adicionar PYTORCH_CUDA_ALLOC_CONF

### Container não inicia
```bash
# Ver logs completos
docker compose logs web

# Rebuild completo
docker compose down -v
docker compose build --no-cache
docker compose up
```

## 📚 Documentação Adicional

- [GPU_SETUP.md](GPU_SETUP.md) - Guia completo de setup
- [DOCKER.md](DOCKER.md) - Instruções Docker atualizadas
- [README.md](README.md) - README principal com info de GPU

## ✅ Checklist de Verificação

- [ ] NVIDIA Container Toolkit instalado
- [ ] `nvidia-smi` funciona no host
- [ ] Docker configurado com runtime NVIDIA
- [ ] Container builda com sucesso
- [ ] `/api/gpu-status` retorna GPU disponível
- [ ] `test_gpu.py` passa todos os testes
- [ ] Transcrição funciona e é mais rápida
