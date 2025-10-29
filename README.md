# Daredevil - API de Transcrição de Áudio 🎙️

API de transcrição de áudio em português usando Django Ninja e Whisper (OpenAI). Suporta múltiplos formatos de áudio, incluindo formatos do WhatsApp e Instagram.

## 🚀 Características

- ✅ Transcrição de alta qualidade usando Whisper
- ✅ Otimizado para português brasileiro
- ✅ **Aceleração por GPU (NVIDIA CUDA)** para processamento até 10x mais rápido
- ✅ Suporte a múltiplos formatos: WhatsApp (.opus, .ogg), Instagram (.mp4, .m4a), e formatos padrão (.mp3, .wav, .flac)
- ✅ Transcrição com timestamps detalhados
- ✅ Processamento em lote
- ✅ API RESTful moderna com Django Ninja
- ✅ Documentação automática (Swagger/OpenAPI)
- ✅ Validação automática com Pydantic
- ✅ Deploy com Docker e suporte a GPU

## 📋 Requisitos

- Python 3.12+
- uv (gerenciador de pacotes)
- ffmpeg (para processamento de áudio)
- **GPU NVIDIA (opcional)**: Para aceleração de processamento com CUDA

### Instalar ffmpeg

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### GPU Support (Opcional)

Para habilitar aceleração por GPU NVIDIA, consulte o guia completo: **[GPU_SETUP.md](GPU_SETUP.md)**

**Benefícios da GPU:**
- Processamento 5-10x mais rápido
- Suporte a modelos maiores (large) sem lentidão
- Melhor para processamento em lote

## 🛠️ Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/daredevil.git
cd daredevil
```

2. **Instale as dependências com uv:**
```bash
uv sync
```

3. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o .env conforme necessário
```

4. **Execute as migrações:**
```bash
uv run python manage.py migrate
```

5. **Inicie o servidor:**
```bash
uv run python manage.py runserver
```

A API estará disponível em: `http://localhost:8000/api/`

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/openapi.json`

## 🎯 Endpoints

### Health Check
```bash
GET /api/health
```

Verifica o status da API e configurações.

### GPU Status
```bash
GET /api/gpu-status
```

Verifica se GPU está disponível e mostra informações de memória.

**Exemplo de resposta com GPU:**
```json
{
  "gpu_available": true,
  "device": "cuda",
  "gpu_count": 1,
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

### Transcrever Áudio
```bash
POST /api/transcribe
```

**Parâmetros:**
- `file`: Arquivo de áudio (multipart/form-data)
- `language`: Código do idioma (padrão: "pt")
- `model`: Modelo Whisper (opcional: tiny, base, small, medium, large)

**Exemplo com curl:**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt"
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

### Transcrever em Lote
```bash
POST /api/transcribe/batch
```

**Parâmetros:**
- `files`: Lista de arquivos de áudio
- `language`: Código do idioma (padrão: "pt")
- `model`: Modelo Whisper (opcional)

### Formatos Suportados
```bash
GET /api/formats
```

Lista todos os formatos de áudio suportados.

## 📁 Formatos Suportados

### WhatsApp
- `.opus`
- `.ogg`
- `.m4a`
- `.aac`

### Instagram
- `.mp4` (extração de áudio)
- `.m4a`
- `.aac`

### Formatos Padrão
- `.mp3`
- `.wav`
- `.flac`
- `.webm`

**Limite de tamanho:** 25MB por arquivo (configurável)

## ⚙️ Configuração

Edite o arquivo `.env` para personalizar:

```env
# Modelo Whisper (tiny, base, small, medium, large)
WHISPER_MODEL=medium

# Tamanho máximo de arquivo em MB
MAX_AUDIO_SIZE_MB=25

# Diretório temporário
TEMP_AUDIO_DIR=/tmp/daredevil

# Habilitar cache
ENABLE_CACHE=true

# Nível de log
LOG_LEVEL=INFO
```

### Modelos Whisper

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

## 🧪 Testando

### Testar configuração da GPU
```bash
uv run python test_gpu.py
```

Este script verifica:
- Se NVIDIA drivers estão instalados
- Se PyTorch detecta a GPU
- Se Whisper pode usar a GPU
- Informações de memória e capacidade da GPU

### Teste rápido com Python
```python
import requests

url = "http://localhost:8000/api/transcribe"
files = {"file": open("audio.mp3", "rb")}
data = {"language": "pt"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Teste com áudio do WhatsApp
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@whatsapp_audio.opus" \
  -F "language=pt"
```

## 🏗️ Estrutura do Projeto

```
daredevil/
├── config/              # Configurações Django
│   ├── settings.py
│   └── urls.py
├── transcription/       # App de transcrição
│   ├── api.py          # Endpoints da API
│   ├── schemas.py      # Modelos Pydantic
│   └── services.py     # Lógica de negócio
├── .env.example        # Exemplo de variáveis de ambiente
├── .github/
│   └── copilot-instructions.md  # Instruções para GitHub Copilot
├── manage.py
├── pyproject.toml
└── README.md
```

## 🔧 Desenvolvimento

### Adicionar nova dependência
```bash
uv add nome-do-pacote
```

### Executar comandos Django
```bash
uv run python manage.py <comando>
```

### Ativar ambiente virtual (opcional)
```bash
source .venv/bin/activate
```

## 📝 Licença

MIT

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.

---

**Nota:** O modelo Whisper será baixado automaticamente na primeira execução (~1-3GB dependendo do modelo escolhido).
