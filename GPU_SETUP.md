# Configuração de GPU para Daredevil API

## Pré-requisitos

### 1. Driver NVIDIA
Certifique-se de ter os drivers NVIDIA instalados no host:
```bash
# Verificar se a GPU está disponível
nvidia-smi
```

### 2. NVIDIA Container Toolkit
Instale o NVIDIA Container Toolkit para permitir que o Docker acesse as GPUs:

#### Ubuntu/Debian
```bash
# Adicionar repositório
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Instalar
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configurar Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### Fedora/RHEL
```bash
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

sudo yum install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### 3. Verificar Instalação
```bash
# Testar GPU com Docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Configuração do Projeto

### docker-compose.yml
A configuração já está habilitada no arquivo `docker-compose.yml`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all  # Usa todas as GPUs disponíveis
          capabilities: [gpu]
```

### Dockerfile
O Dockerfile foi atualizado para usar a imagem base `nvidia/cuda:12.1.0-base-ubuntu22.04` que inclui os drivers CUDA necessários.

## Uso

### Iniciar o serviço com GPU
```bash
docker-compose up --build
```

### Verificar se a GPU está sendo usada
```bash
# Em outro terminal, enquanto o container está rodando
docker exec daredevil_web python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}'); print(f'GPUs: {torch.cuda.device_count()}')"
```

### Monitorar uso da GPU
```bash
# No host
watch -n 1 nvidia-smi
```

## Configuração Avançada

### Usar GPU específica
Se você tem múltiplas GPUs e quer usar apenas uma:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0']  # Usar apenas GPU 0
          capabilities: [gpu]
```

### Limitar GPUs
Para usar apenas 2 GPUs:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 2
          capabilities: [gpu]
```

## Otimizações para Whisper com GPU

### 1. Instalar PyTorch com CUDA
No seu `pyproject.toml`, certifique-se de ter PyTorch com suporte CUDA:
```bash
uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 2. Configurar Whisper para usar GPU
No código de transcrição, o Whisper detectará automaticamente a GPU:
```python
import whisper
import torch

# Carregar modelo na GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("medium", device=device)
```

### 3. Variáveis de Ambiente
Adicione ao `docker-compose.yml` se necessário:
```yaml
environment:
  - CUDA_VISIBLE_DEVICES=0  # Usar apenas GPU 0
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Otimizar memória
```

## Troubleshooting

### Erro: "could not select device driver"
```bash
# Reiniciar Docker
sudo systemctl restart docker

# Verificar se o runtime está configurado
docker info | grep -i runtime
```

### Erro: "CUDA out of memory"
- Usar modelo Whisper menor (base ou small)
- Processar áudios em lotes menores
- Adicionar configuração de memória CUDA

### GPU não detectada no container
```bash
# Verificar logs
docker logs daredevil_web

# Testar manualmente
docker exec -it daredevil_web nvidia-smi
```

## Performance Esperada

Com GPU habilitada, você deve ver:
- **Whisper base**: ~5-10x mais rápido
- **Whisper small**: ~4-8x mais rápido
- **Whisper medium**: ~3-6x mais rápido
- **Whisper large**: ~2-4x mais rápido

O ganho exato depende da sua GPU e da duração do áudio.

## Requisitos de Hardware

### Memória GPU Recomendada
- **Whisper base**: 1GB VRAM
- **Whisper small**: 2GB VRAM
- **Whisper medium**: 5GB VRAM
- **Whisper large**: 10GB VRAM

### GPUs Testadas
- NVIDIA RTX 3060 (12GB): Excelente performance
- NVIDIA RTX 4090 (24GB): Performance máxima
- NVIDIA T4 (16GB): Ótima para cloud
- NVIDIA A100 (40GB): Performance máxima para produção
