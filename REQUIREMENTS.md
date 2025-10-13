# Requisitos do Sistema - Daredevil API

## Software Necessário

### 1. Python
- **Versão**: 3.12 ou superior
- **Verificar instalação**: `python3 --version`

### 2. uv (Gerenciador de Pacotes)
- **Instalação**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
- **Verificar**: `uv --version`

### 3. ffmpeg (Processamento de Áudio)
- **Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

- **macOS**:
```bash
brew install ffmpeg
```

- **Arch Linux**:
```bash
sudo pacman -S ffmpeg
```

- **Verificar**: `ffmpeg -version`

## Requisitos de Hardware

### Mínimo (modelo `tiny` ou `base`)
- **RAM**: 2GB disponível
- **Disco**: 500MB para modelo + 1GB para cache
- **CPU**: Qualquer processador moderno

### Recomendado (modelo `medium`)
- **RAM**: 6GB disponível
- **Disco**: 1GB para modelo + 2GB para cache
- **CPU**: 4+ cores
- **GPU**: Opcional, mas acelera significativamente (CUDA)

### Performance (modelo `large`)
- **RAM**: 12GB disponível
- **Disco**: 2GB para modelo + 3GB para cache
- **CPU**: 8+ cores ou GPU NVIDIA com CUDA
- **GPU**: Altamente recomendado

## Configuração com GPU (Opcional)

Para usar GPU NVIDIA e acelerar a transcrição:

1. **Instalar CUDA Toolkit**:
```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /"
sudo apt-get update
sudo apt-get -y install cuda
```

2. **Instalar PyTorch com CUDA**:
```bash
cd /home/marcus/desenvolvimento/daredevil
uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

3. **Verificar GPU**:
```bash
nvidia-smi
```

## Portas Necessárias

- **8000**: Servidor de desenvolvimento Django (padrão)
- Pode ser alterada: `uv run python manage.py runserver 0.0.0.0:8080`

## Permissões

### Diretório Temporário
O diretório `/tmp/daredevil` precisa de permissão de escrita:
```bash
mkdir -p /tmp/daredevil
chmod 755 /tmp/daredevil
```

### Alternativa (usuário local)
Edite `.env`:
```
TEMP_AUDIO_DIR=~/.cache/daredevil
```

## Dependências Python

Todas as dependências são instaladas automaticamente com:
```bash
uv sync
```

Principais pacotes:
- django (5.2+)
- django-ninja (1.3+)
- openai-whisper
- pydub
- torch
- numpy
- ffmpeg-python

## Verificação da Instalação

Execute o script de verificação:
```bash
./scripts/check_system.sh
```

Ou manualmente:
```bash
# Verificar Python
python3 --version

# Verificar uv
uv --version

# Verificar ffmpeg
ffmpeg -version

# Verificar dependências Python
uv run python -c "import django; import whisper; import pydub; print('✅ Todas as dependências OK')"

# Iniciar servidor
uv run python manage.py runserver
```

## Troubleshooting

### Erro: "ffmpeg not found"
Instale ffmpeg conforme instruções acima para seu sistema operacional.

### Erro: "CUDA not available"
Normal se não tiver GPU NVIDIA. O Whisper funcionará na CPU (mais lento).

### Erro: "Out of memory"
- Use um modelo menor (tiny, base, small)
- Configure `WHISPER_MODEL=small` no `.env`
- Aumente a RAM disponível

### Erro: "Port 8000 already in use"
Use outra porta:
```bash
uv run python manage.py runserver 8001
```

## Performance Estimada

### CPU Intel i5 (4 cores)
- tiny: ~0.1x realtime (10s áudio = 1s processamento)
- small: ~0.5x realtime
- medium: ~2x realtime

### GPU NVIDIA RTX 3060
- tiny: ~0.01x realtime (muito rápido)
- small: ~0.05x realtime
- medium: ~0.2x realtime
- large: ~0.5x realtime

*Nota: Tempos variam conforme qualidade do áudio e configurações*
