# Daredevil - API de Transcrição de Áudio 🎙️

API de transcrição de áudio em português usando Django Ninja e Whisper (OpenAI). Suporta múltiplos formatos de áudio, incluindo formatos do WhatsApp e Instagram, com pós-processamento inteligente.

## 🚀 Características

- ✅ Transcrição de alta qualidade usando Whisper
- ✅ Otimizado para português brasileiro
- ✅ **NOVO: Correção automática de gramática e pontuação**
- ✅ **NOVO: Identificação de interlocutores em conversas**
- ✅ **NOVO: Remoção de hesitações (é, ah, er, uhm)**
- ✅ Suporte a múltiplos formatos: WhatsApp (.opus, .ogg), Instagram (.mp4, .m4a), e formatos padrão (.mp3, .wav, .flac)
- ✅ Transcrição com timestamps detalhados
- ✅ Processamento em lote
- ✅ API RESTful moderna com Django Ninja
- ✅ Documentação automática (Swagger/OpenAPI)
- ✅ Validação automática com Pydantic

## 📋 Requisitos

- Python 3.12+
- uv (gerenciador de pacotes)
- ffmpeg (para processamento de áudio)

### Instalar ffmpeg

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

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

### Transcrever Áudio
```bash
POST /api/transcribe
```

**Parâmetros:**
- `file`: Arquivo de áudio (multipart/form-data)
- `language`: Código do idioma (padrão: "pt")
- `model`: Modelo Whisper (opcional: tiny, base, small, medium, large)
- `post_process`: Aplicar pós-processamento (padrão: true)
- `correct_grammar`: Corrigir gramática e pontuação (padrão: true)
- `identify_speakers`: Identificar interlocutores (padrão: true)
- `clean_hesitations`: Remover hesitações (padrão: true)

**Exemplo com curl (básico):**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt"
```

**Exemplo com curl (com pós-processamento desabilitado):**
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt" \
  -F "post_process=false"
```

**Resposta (com pós-processamento):**
```json
{
  "success": true,
  "transcription": {
    "text": "Speaker_A: Olá, como você está?\nSpeaker_B: Estou bem, obrigado.",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Olá, como você está?",
        "original_text": "olá como voce está",
        "speaker_id": "Speaker_A",
        "confidence": 0.95
      },
      {
        "start": 3.0,
        "end": 5.0,
        "text": "Estou bem, obrigado.",
        "original_text": "estou bem obrigado",
        "speaker_id": "Speaker_B",
        "confidence": 0.93
      }
    ],
    "language": "pt",
    "duration": 5.0,
    "formatted_conversation": "Speaker_A: Olá, como você está?\nSpeaker_B: Estou bem, obrigado.",
    "post_processed": true
  },
  "processing_time": 3.2,
  "audio_info": {
    "format": "mp3",
    "duration": 5.0,
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
- `post_process`: Aplicar pós-processamento (padrão: true)
- `correct_grammar`: Corrigir gramática e pontuação (padrão: true)
- `identify_speakers`: Identificar interlocutores (padrão: true)
- `clean_hesitations`: Remover hesitações (padrão: true)

### Formatos Suportados
```bash
GET /api/formats
```

Lista todos os formatos de áudio suportados.

## 🧠 Pós-Processamento Inteligente

### Correção de Gramática e Pontuação

O sistema utiliza **LanguageTool** para corrigir erros gramaticais e de pontuação em português:

- Correção automática de erros comuns
- Ajuste de capitalização
- Melhoria da pontuação
- Otimizado para português brasileiro

**Exemplo:**
```
Entrada:  "ola como vai voce"
Saída:    "Olá, como vai você?"
```

### Identificação de Interlocutores

Algoritmo inteligente que identifica diferentes pessoas falando baseado em:

- **Pausas longas** (> 1 segundo entre segmentos)
- **Padrões de conversa** (perguntas e respostas)
- **Mudanças de contexto linguístico**

**Exemplo:**
```
Speaker_A: Olá, tudo bem?
Speaker_B: Sim, estou bem. E você?
Speaker_A: Também estou bem, obrigado.
```

### Remoção de Hesitações

Remove automaticamente hesitações comuns em português:

- `é`, `ah`, `oh`, `uh`, `uhm`
- `er`, `hmm`, `né`

**Exemplo:**
```
Entrada:  "Olá, é, eu queria ah falar sobre er o projeto"
Saída:    "Olá, eu queria falar sobre o projeto"
```

### Demonstração

Execute o script de demonstração para ver todos os recursos:

```bash
uv run python demo_post_processing.py
```

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

| Modelo | Tamanho | RAM Necessária | Velocidade | Qualidade |
|--------|---------|----------------|------------|-----------|
| tiny   | ~39 MB  | ~1 GB          | Muito rápido | Básica |
| base   | ~74 MB  | ~1 GB          | Rápido     | Boa    |
| small  | ~244 MB | ~2 GB          | Moderado   | Muito boa |
| medium | ~769 MB | ~5 GB          | Lento      | Excelente |
| large  | ~1.5 GB | ~10 GB         | Muito lento | Melhor |

**Recomendação:** Use `medium` para melhor equilíbrio entre qualidade e velocidade.

## 🧪 Testando

### Executar testes unitários
```bash
# Todos os testes
uv run python manage.py test transcription

# Apenas testes de pós-processamento
uv run python -m unittest transcription.test_post_processing
```

### Demonstração interativa
```bash
# Ver todos os recursos em ação
uv run python demo_post_processing.py
```

### Teste rápido com Python
```python
import requests

url = "http://localhost:8000/api/transcribe"
files = {"file": open("audio.mp3", "rb")}
data = {
    "language": "pt",
    "post_process": "true",
    "identify_speakers": "true",
    "correct_grammar": "true"
}

response = requests.post(url, files=files, data=data)
result = response.json()

# Ver texto completo com interlocutores
print(result['transcription']['formatted_conversation'])
```

### Teste com áudio do WhatsApp
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@whatsapp_audio.opus" \
  -F "language=pt" \
  -F "identify_speakers=true"
```

## 🏗️ Estrutura do Projeto

```
daredevil/
├── config/                      # Configurações Django
│   ├── settings.py
│   └── urls.py
├── transcription/               # App de transcrição
│   ├── api.py                  # Endpoints da API
│   ├── schemas.py              # Modelos Pydantic
│   ├── services.py             # Lógica de transcrição
│   ├── post_processing.py      # Pós-processamento de texto
│   └── test_post_processing.py # Testes unitários
├── demo_post_processing.py      # Script de demonstração
├── .env.example                 # Exemplo de variáveis de ambiente
├── .github/
│   └── copilot-instructions.md # Instruções para GitHub Copilot
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
