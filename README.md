# Daredevil - API de Transcrição de Áudio e Vídeo 🎙️

API completa de transcrição de áudio e vídeo em português brasileiro usando Django Ninja e Whisper (OpenAI). Suporta múltiplos formatos, aceleração por GPU NVIDIA, e processamento inteligente de texto.

## ⚡ Performance Otimizada (NOVO!)

**Melhorias implementadas para velocidade 2-3x maior:**

- 🚀 **Cache Inteligente**: Resultados salvos automaticamente (LRU + TTL)
- 🎯 **GPU Persistente**: Modelo mantido em memória GPU entre requisições
- 🔄 **Processamento Assíncrono**: Celery + Redis para jobs em background
- 📊 **Monitoramento Real-time**: Status de GPU e cache via API
- 🔁 **Retry Automático**: Jobs falhos são retentados automaticamente
- 📢 **Webhooks**: Notificação automática quando transcrição completa

**Performance esperada:**
- Audio 1min: ~12s → **<8s** (cache: **<0.1s**)
- Video 5min: ~60s → **<45s** (cache: **<0.1s**)
- Video 30min: ~5min → **<2min**

📖 **[Ver documentação completa de otimizações →](PERFORMANCE_OPTIMIZATION.md)**

## 🚀 Características Principais

- ✅ **Transcrição de alta qualidade** usando Whisper (OpenAI)
- ✅ **Otimizado para português brasileiro** com pós-processamento automático
- ✅ **Aceleração por GPU NVIDIA (CUDA 12.1)** - processamento até 10x mais rápido
- ✅ **Cache inteligente** - resultados instantâneos para arquivos já processados
- ✅ **Processamento assíncrono** - ideal para arquivos grandes e lotes
- ✅ **Suporte a vídeos** - extração automática de áudio de 12 formatos de vídeo
- ✅ **Suporte a múltiplos formatos de áudio** - WhatsApp, Instagram e formatos padrão
- ✅ **Transcrição com timestamps detalhados** - precisão ao nível de segmento
- ✅ **Processamento em lote** - múltiplos arquivos simultaneamente
- ✅ **API RESTful moderna** com Django Ninja
- ✅ **Documentação automática** (Swagger/OpenAPI)
- ✅ **Validação automática** com Pydantic
- ✅ **Deploy com Docker** - pronto para produção
- ✅ **Limite de 500MB** por arquivo

## 📋 Índice

- [Requisitos](#-requisitos)
- [Instalação](#️-instalação)
- [Docker](#-docker)
- [Uso da API](#-uso-da-api)
- [Formatos Suportados](#-formatos-suportados)
- [GPU NVIDIA](#-gpu-nvidia)
- [Português Brasileiro](#-português-brasileiro)
- [Processamento de Vídeos](#-processamento-de-vídeos)
- [Configuração](#️-configuração)
- [Testes](#-testes)
- [Performance](#-performance)
- [Troubleshooting](#-troubleshooting)
- [Estrutura do Projeto](#️-estrutura-do-projeto)

## 📋 Requisitos

### Software Necessário

- **Python 3.12+**
- **uv** (gerenciador de pacotes Python)
- **ffmpeg** (para processamento de áudio/vídeo)

### Requisitos de Hardware

#### Mínimo (modelo `tiny` ou `base`)
- RAM: 2GB disponível
- Disco: 500MB para modelo + 1GB para cache
- CPU: Qualquer processador moderno

#### Recomendado (modelo `medium`)
- RAM: 6GB disponível
- Disco: 1GB para modelo + 2GB para cache
- CPU: 4+ cores
- **GPU NVIDIA (opcional)**: Acelera significativamente o processamento

#### Performance (modelo `large`)
- RAM: 12GB disponível
- Disco: 2GB para modelo + 3GB para cache
- CPU: 8+ cores ou GPU NVIDIA com CUDA
- **GPU NVIDIA**: Altamente recomendado

### Instalar Dependências do Sistema

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# Verificar instalação
ffmpeg -version
```

### Instalar uv (Gerenciador de Pacotes Python)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 🛠️ Instalação

### Opção 1: Instalação Local

```bash
# 1. Clone o repositório
git clone https://github.com/nextmarte/daredevil.git
cd daredevil

# 2. Instale as dependências com uv
uv sync

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env conforme necessário

# 4. Execute as migrações
uv run python manage.py migrate

# 5. Inicie o servidor
uv run python manage.py runserver
```

A API estará disponível em: `http://localhost:8000/api/`

### Opção 2: Docker (Recomendado)

Veja a seção [Docker](#-docker) abaixo.

## 🐳 Docker

### Quick Start

```bash
# Build e iniciar container
docker compose up -d

# Ver logs
docker compose logs -f web

# Parar container
docker compose down
```

O servidor estará disponível em: `http://localhost:8511/api/`

### Com GPU NVIDIA

Para usar GPU, você precisa ter o NVIDIA Container Toolkit instalado:

```bash
# Ubuntu/Debian - Instalar NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verificar instalação
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

Então, basta iniciar o container normalmente:

```bash
docker compose up -d
```

### Comandos Úteis do Docker

```bash
# Parar container
docker compose down

# Rebuild completo (força reconstrução)
docker compose build --no-cache web

# Restart
docker compose restart web

# Ver status
docker compose ps

# Entrar no container
docker exec -it daredevil_web /bin/bash

# Ver logs
docker compose logs -f web

# Executar comando no container
docker exec daredevil_web uv run python manage.py <comando>
```

## 🎯 Uso da API

### Documentação Automática

Após iniciar o servidor, acesse:

- **Swagger UI**: `http://localhost:8000/api/docs` (ou `http://localhost:8511/api/docs` no Docker)
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/openapi.json`

### Endpoints Principais

#### Health Check

```bash
GET /api/health
```

Verifica o status da API e configurações.

**Exemplo:**
```bash
curl http://localhost:8000/api/health
```

#### GPU Status

```bash
GET /api/gpu-status
```

Verifica se GPU está disponível e mostra informações de memória.

**Exemplo de resposta com GPU:**
```json
{
  "gpu_available": true,
  "device": "cuda",
  "gpu_count": 2,
  "gpus": [
    {
      "id": 0,
      "name": "NVIDIA GeForce RTX 3060",
      "memory_allocated_gb": 2.5,
      "memory_reserved_gb": 3.0,
      "memory_total_gb": 12.0,
      "memory_free_gb": 9.0,
      "compute_capability": "8.6"
    }
  ]
}
```

#### Listar Formatos Suportados

```bash
GET /api/formats
```

Lista todos os formatos de áudio e vídeo suportados.

**Resposta:**
```json
{
  "audio_formats": ["aac", "m4a", "mp3", "ogg", "opus", "wav", "flac", "webm", "weba"],
  "video_formats": ["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "ogv", "ts", "mts", "m2ts", "3gp", "f4v", "asf"],
  "all_formats": ["aac", "m4a", ...],
  "max_file_size_mb": 500
}
```

#### Transcrever Áudio ou Vídeo

```bash
POST /api/transcribe
```

**Parâmetros:**
- `file`: Arquivo de áudio ou vídeo (multipart/form-data)
- `language`: Código do idioma (padrão: "pt" - português brasileiro)
- `model`: Modelo Whisper (opcional: tiny, base, small, medium, large)

**Exemplo com curl - Áudio:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt"
```

**Exemplo com curl - Vídeo:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@video.mp4" \
  -F "language=pt"
```

**Exemplo com Python:**
```python
import requests

url = "http://localhost:8000/api/transcribe"
files = {"file": open("audio.mp3", "rb")}
data = {"language": "pt"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Resposta:**
```json
{
  "success": true,
  "transcription": {
    "text": "Olá, como você está?",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Olá, como você está?",
        "confidence": 0.95
      }
    ],
    "language": "pt",
    "duration": 2.5
  },
  "processing_time": 3.2,
  "audio_info": {
    "format": "mp3",
    "duration": 2.5,
    "sample_rate": 44100,
    "channels": 2,
    "file_size_mb": 0.5
  }
}
```

#### Transcrever em Lote

```bash
POST /api/transcribe/batch
```

**Parâmetros:**
- `files`: Lista de arquivos de áudio/vídeo
- `language`: Código do idioma (padrão: "pt")
- `model`: Modelo Whisper (opcional)

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/transcribe/batch" \
  -F "files=@audio1.mp3" \
  -F "files=@video2.mp4" \
  -F "files=@audio3.wav" \
  -F "language=pt"
```

#### Transcrever Assíncrono (NOVO! ⚡)

```bash
POST /api/transcribe/async
```

Para arquivos grandes ou quando não quer bloquear a requisição.

**Parâmetros:**
- `file`: Arquivo de áudio ou vídeo
- `language`: Código do idioma (padrão: "pt")
- `model`: Modelo Whisper (opcional)
- `webhook_url`: URL para notificação quando concluir (opcional)

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/transcribe/async" \
  -F "file=@video_longo.mp4" \
  -F "language=pt" \
  -F "webhook_url=https://meusite.com/webhook"
```

**Resposta:**
```json
{
  "success": true,
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_url": "/api/transcribe/async/status/a1b2c3d4...",
  "message": "Transcrição iniciada. Use task_id para consultar o status.",
  "submission_time": 0.15
}
```

#### Consultar Status de Tarefa Assíncrona (NOVO! ⚡)

```bash
GET /api/transcribe/async/status/{task_id}
```

**Exemplo:**
```bash
curl http://localhost:8000/api/transcribe/async/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Resposta (concluída):**
```json
{
  "task_id": "a1b2c3d4...",
  "state": "SUCCESS",
  "result": {
    "success": true,
    "transcription": {
      "text": "transcrição completa...",
      "segments": [...],
      "language": "pt"
    },
    "processing_time": 45.2
  },
  "message": "Transcrição concluída"
}
```

#### Cancelar Tarefa Assíncrona (NOVO! ⚡)

```bash
DELETE /api/transcribe/async/{task_id}
```

#### Estatísticas de Cache (NOVO! ⚡)

```bash
GET /api/cache-stats
```

Retorna estatísticas do cache (hits, misses, hit rate).

**Resposta:**
```json
{
  "cache_enabled": true,
  "size": 25,
  "max_size": 100,
  "hits": 150,
  "misses": 50,
  "hit_rate": 75.0,
  "ttl_seconds": 3600
}
```

#### Limpar Cache (NOVO! ⚡)

```bash
POST /api/cache/clear
```

Remove todos os itens do cache.

## 📁 Formatos Suportados

### Áudio (9 formatos)

- `.aac` - Advanced Audio Coding
- `.m4a` - MPEG-4 Audio
- `.mp3` - MPEG Audio Layer 3
- `.ogg` - Ogg Vorbis
- `.opus` - Opus Audio (WhatsApp)
- `.wav` - Waveform Audio
- `.flac` - Free Lossless Audio Codec
- `.webm` - WebM Audio
- `.weba` - WebM Audio

### Vídeo (14 formatos)

O sistema extrai automaticamente o áudio de arquivos de vídeo:

- `.mp4` - MPEG-4 Video (WhatsApp, Instagram)
- `.avi` - Audio Video Interleave
- `.mov` - QuickTime (iPhone, macOS)
- `.mkv` - Matroska
- `.flv` - Flash Video
- `.wmv` - Windows Media Video
- `.webm` - WebM Video
- `.ogv` - Ogg Video
- `.ts` - MPEG Transport Stream
- `.mts` - MPEG Transport Stream (Sony)
- `.m2ts` - MPEG-2 Transport Stream (Blu-ray)
- `.3gp` - 3GPP (celulares)
- `.f4v` - Flash Video
- `.asf` - Advanced Systems Format

**Total: 23 formatos suportados**

**Limite de tamanho:** 500MB por arquivo (configurável)

## 🎮 GPU NVIDIA

### Benefícios da GPU

- ⚡ Processamento **5-10x mais rápido**
- 🚀 Suporte a modelos maiores (large) sem lentidão
- 📦 Melhor para processamento em lote
- 💾 Uso eficiente de memória com FP16

### Configuração

O projeto já está configurado para usar GPU automaticamente quando disponível. O Dockerfile usa a imagem base `nvidia/cuda:12.1.0-base-ubuntu22.04` e o `docker-compose.yml` já tem a configuração de GPU:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all  # Usa todas as GPUs disponíveis
          capabilities: [gpu]
```

### Verificar GPU

```bash
# No host
nvidia-smi

# No container Docker
docker exec daredevil_web nvidia-smi

# Via API
curl http://localhost:8511/api/gpu-status
```

### Modelos Whisper e Requisitos de GPU

| Modelo | Tamanho | RAM Necessária | GPU VRAM | Velocidade (CPU) | Velocidade (GPU) | Qualidade |
|--------|---------|----------------|----------|------------------|------------------|-----------|
| tiny   | ~39 MB  | ~1 GB          | ~1 GB    | Muito rápido     | Extremamente rápido | Básica |
| base   | ~74 MB  | ~1 GB          | ~1 GB    | Rápido           | Muito rápido     | Boa    |
| small  | ~244 MB | ~2 GB          | ~2 GB    | Moderado         | Rápido           | Muito boa |
| medium | ~769 MB | ~5 GB          | ~5 GB    | Lento            | Moderado         | Excelente |
| large  | ~1.5 GB | ~10 GB         | ~10 GB   | Muito lento      | Moderado         | Melhor |

**Recomendação:** 
- Com CPU: Use `small` ou `medium`
- Com GPU: Use `medium` ou `large` para melhor qualidade

### Performance Esperada com GPU

Com GPU habilitada (RTX 3060 ou superior):

- **Whisper base**: ~5-10x mais rápido
- **Whisper small**: ~4-8x mais rápido
- **Whisper medium**: ~3-6x mais rápido
- **Whisper large**: ~2-4x mais rápido

**Exemplo prático:**
- Áudio de 5 minutos com modelo medium:
  - **CPU**: ~45-60 segundos
  - **GPU**: ~8-15 segundos

## 🇧🇷 Português Brasileiro

### Funcionalidades

A API foi totalmente otimizada para português brasileiro:

- ✅ **Português como idioma padrão** - não precisa especificar language=pt
- ✅ **Pós-processamento inteligente** de texto
- ✅ **Remoção de hesitações** comuns (tipo, sabe, entendeu, né, hã, etc.)
- ✅ **Normalização de pontuação** e capitalização
- ✅ **Expansão de abreviações** (Sr., Ltda., etc.)
- ✅ **Correção de erros comuns** do Whisper em português

### Exemplo de Processamento

**Entrada (bruta do Whisper):**
```
Então tipo você sabe né isso é bem importante hã . O sr joão trabalha na ltda .
```

**Saída (processada):**
```
Então, você sabe, isso é bem importante. O Sr. João trabalha na Ltda.
```

### Melhorias Aplicadas

#### 1. Remoção de Hesitações
Remove palavras de hesitação comuns: tipo, sabe, entendeu, né, tá, hã, hm, hmm, ah, é, etc.

#### 2. Normalização de Pontuação
- Remove espaços antes de pontuação
- Adiciona espaço após pontuação
- Corrige múltiplas pontuações

#### 3. Capitalização Correta
- Primeira letra do texto maiúscula
- Primeira letra após pontuação final
- Nomes próprios reconhecidos

#### 4. Expansão de Abreviações
- sr → Sr.
- sra → Sra.
- dr → Dr.
- ltda → Ltda.
- etc → Etc.

### Usar Outro Idioma

Você ainda pode transcrever em outros idiomas:

```bash
# Inglês
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=en"

# Espanhol
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=es"
```

## 🎥 Processamento de Vídeos

### Como Funciona

Quando um arquivo de vídeo é enviado, o sistema automaticamente:

1. ✅ Valida a integridade do arquivo com `ffprobe`
2. ✅ Extrai o áudio em qualidade otimizada (16kHz, mono, WAV)
3. ✅ Transcreve o áudio com Whisper
4. ✅ Aplica processamento de português brasileiro
5. ✅ Retorna transcrição com timestamps
6. ✅ Limpa arquivos temporários

### Exemplo de Uso

```bash
# Transcrever vídeo do Instagram
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@instagram_video.mp4" \
  -F "language=pt"

# Transcrever vídeo do iPhone
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@iphone_video.mov" \
  -F "model=large"
```

### Performance com Vídeos

Tempos típicos com GPU RTX 3060:

| Duração do Vídeo | Tempo de Processamento |
|------------------|------------------------|
| 1 minuto         | ~15-20 segundos        |
| 5 minutos        | ~30-40 segundos        |
| 30 minutos       | ~2-3 minutos           |
| 1 hora           | ~4-6 minutos           |

**Fatores que afetam:** Tamanho/resolução do vídeo, bitrate de áudio, modelo Whisper usado, disponibilidade de GPU.

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Modelo Whisper (tiny, base, small, medium, large)
WHISPER_MODEL=medium

# Idioma padrão
WHISPER_LANGUAGE=pt

# Tamanho máximo de arquivo em MB
MAX_AUDIO_SIZE_MB=500

# Diretório temporário
TEMP_AUDIO_DIR=/tmp/daredevil

# Habilitar cache
ENABLE_CACHE=true

# Nível de log
LOG_LEVEL=INFO

# Django
DEBUG=0
ALLOWED_HOSTS=*
SECRET_KEY=your-secret-key-here

# Locale (Português Brasileiro)
LANGUAGE=pt_BR.UTF-8
LANG=pt_BR.UTF-8
LC_ALL=pt_BR.UTF-8
```

### Docker Compose

Edite `docker-compose.yml` para ajustar configurações:

```yaml
environment:
  - WHISPER_MODEL=medium
  - WHISPER_LANGUAGE=pt
  - MAX_AUDIO_SIZE_MB=500
  - LANGUAGE=pt_BR.UTF-8
  - LANG=pt_BR.UTF-8
  - LC_ALL=pt_BR.UTF-8
```

### Ajustar Limite de Upload

Para aumentar o limite além de 500MB:

```env
# No .env
MAX_AUDIO_SIZE_MB=1000  # 1GB
```

Depois reinicie o servidor ou container.

## 🧪 Testes

### Testes Disponíveis

```bash
# Testar configuração da GPU
uv run python test_gpu.py

# Testar português brasileiro
uv run python test_portuguese_br.py

# Testar suporte a vídeos
uv run python test_video_support.py

# Testar processamento de português
uv run python test_pt_processing.py

# Testar API completa
uv run python test_api.py
```

### Teste Rápido via curl

```bash
# Health check
curl http://localhost:8000/api/health

# Status da GPU
curl http://localhost:8000/api/gpu-status

# Listar formatos
curl http://localhost:8000/api/formats

# Transcrever áudio de teste
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@seu_audio.mp3" \
  -F "language=pt"
```

### Teste com Python

```python
import requests

def test_transcription():
    url = "http://localhost:8000/api/transcribe"
    files = {"file": open("audio.mp3", "rb")}
    data = {"language": "pt"}
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    if result["success"]:
        print(f"✅ Transcrição: {result['transcription']['text']}")
        print(f"⏱️ Tempo: {result['processing_time']:.2f}s")
    else:
        print(f"❌ Erro: {result.get('error')}")

test_transcription()
```

## 📊 Performance

### Tempos de Transcrição (1 minuto de áudio)

| Modelo | CPU (8 cores) | GPU (RTX 3060) | Speedup |
|--------|---------------|----------------|---------|
| tiny   | ~30s          | ~3-5s          | 6-10x   |
| base   | ~45s          | ~5-8s          | 6-9x    |
| small  | ~60s          | ~8-12s         | 6-8x    |
| medium | ~90s          | ~12-18s        | 6-7x    |
| large  | ~120s         | ~18-25s        | 5-7x    |

### Benchmarks Reais

Com GPU RTX 3060 (12GB):

- **Áudio WhatsApp (30s, opus)**: ~5-8s
- **Vídeo Instagram (1min, mp4)**: ~15-20s
- **Podcast (30min, mp3)**: ~2-3min
- **Entrevista (1h, wav)**: ~4-6min

### Otimizações Ativas

- ✅ GPU NVIDIA com CUDA 12.1
- ✅ FP16 em GPU (economiza 50% de memória)
- ✅ Português como padrão (sem overhead de detecção)
- ✅ Pós-processamento otimizado (~0.1-0.2s overhead)
- ✅ Cache de modelos em memória GPU
- ✅ Processamento paralelo de áudio (ffmpeg multi-thread)

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. "Connection refused"

**Problema:** Servidor não está rodando.

**Solução:**
```bash
# Local
uv run python manage.py runserver

# Docker
docker compose up -d
docker compose logs -f web
```

#### 2. "File format not supported"

**Problema:** Formato de arquivo inválido.

**Solução:**
```bash
# Verificar formatos suportados
curl http://localhost:8000/api/formats

# Converter arquivo
ffmpeg -i input.xyz -c:a libmp3lame output.mp3
```

#### 3. "File too large"

**Problema:** Arquivo maior que o limite (padrão 500MB).

**Solução:**
```bash
# Aumentar limite no .env
MAX_AUDIO_SIZE_MB=1000

# Ou comprimir arquivo
ffmpeg -i input.mp4 -c:v libx264 -crf 28 output.mp4
```

#### 4. GPU não detectada

**Problema:** GPU não disponível no container.

**Solução:**
```bash
# Verificar drivers NVIDIA
nvidia-smi

# Verificar runtime Docker
docker info | grep -i runtime

# Reinstalar NVIDIA Container Toolkit (veja seção GPU)
```

#### 5. Transcrição muito lenta

**Problema:** Modelo muito grande para CPU.

**Solução:**
```env
# Usar modelo menor no .env
WHISPER_MODEL=small
```

#### 6. "Out of memory"

**Problema:** Memória insuficiente para modelo.

**Solução:**
```env
# Usar modelo menor
WHISPER_MODEL=base

# Ou aumentar swap/RAM
```

#### 7. Vídeo sem áudio

**Problema:** Vídeo não possui faixa de áudio.

**Solução:**
```bash
# Verificar se vídeo tem áudio
ffprobe -v error -select_streams a video.mp4

# Adicionar áudio ao vídeo
ffmpeg -i video.mp4 -i audio.mp3 -c copy output.mp4
```

### Logs de Debug

```bash
# Ver logs do Django (local)
tail -f /tmp/daredevil/django.log

# Ver logs do Docker
docker compose logs -f web

# Ver logs de erro
docker compose logs web | grep -i error

# Modo debug (no .env)
DEBUG=1
LOG_LEVEL=DEBUG
```

## 🏗️ Estrutura do Projeto

```
daredevil/
├── config/                      # Configurações Django
│   ├── settings.py             # Configurações principais
│   ├── urls.py                 # URLs do projeto
│   └── wsgi.py                 # WSGI para produção
├── transcription/              # App de transcrição
│   ├── api.py                  # Endpoints da API
│   ├── schemas.py              # Modelos Pydantic
│   ├── services.py             # Lógica de transcrição
│   ├── audio_processor.py      # Processamento de áudio
│   ├── video_processor.py      # Processamento de vídeo
│   └── portuguese_processor.py # Pós-processamento PT-BR
├── .env.example                # Exemplo de variáveis
├── .github/
│   └── copilot-instructions.md # Instruções para Copilot
├── Dockerfile                  # Imagem Docker
├── docker-compose.yml          # Orquestração Docker
├── docker-entrypoint.sh        # Script de inicialização
├── manage.py                   # Django management
├── pyproject.toml              # Dependências (UV)
├── uv.lock                     # Lock de dependências
├── README.md                   # Este arquivo
├── test_*.py                   # Scripts de teste
└── examples.py                 # Exemplos de uso
```

## 🔧 Desenvolvimento

### Adicionar Nova Dependência

```bash
uv add nome-do-pacote
```

### Executar Comandos Django

```bash
# Sempre use 'uv run' antes de comandos Python
uv run python manage.py <comando>

# Exemplos:
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py shell
```

### Comandos uv Úteis

```bash
# Sincronizar ambiente
uv sync

# Adicionar dependência
uv add package-name

# Remover dependência
uv remove package-name

# Atualizar dependências
uv sync --upgrade

# Executar script
uv run python script.py

# Shell Python
uv run python

# Ver versão
uv --version
```

### Docker e UV

**CRÍTICO:** No ambiente Docker, sempre use `uv run` antes de comandos Python:

```bash
# ✅ CORRETO
docker exec daredevil_web uv run python manage.py migrate

# ❌ ERRADO (não encontrará os pacotes)
docker exec daredevil_web python manage.py migrate
```

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

## 🙏 Agradecimentos

- [OpenAI Whisper](https://github.com/openai/whisper) - Modelo de transcrição
- [Django Ninja](https://django-ninja.rest-framework.com/) - Framework de API
- [UV](https://github.com/astral-sh/uv) - Gerenciador de pacotes
- [FFmpeg](https://ffmpeg.org/) - Processamento de mídia

---

**Desenvolvido com ❤️ para a comunidade brasileira**

**Nota:** O modelo Whisper será baixado automaticamente na primeira execução (~1-3GB dependendo do modelo escolhido).
