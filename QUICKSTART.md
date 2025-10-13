# 🚀 Guia de Início Rápido - Daredevil API

## Instalação Rápida (5 minutos)

### 1. Pré-requisitos
```bash
# Instalar ffmpeg
sudo apt-get install ffmpeg  # Ubuntu/Debian
# ou
brew install ffmpeg  # macOS

# Verificar
ffmpeg -version
python3 --version  # Precisa 3.12+
```

### 2. Configurar Projeto
```bash
# Clonar repositório
cd ~/desenvolvimento/daredevil

# Instalar dependências
uv sync

# Copiar configurações
cp .env.example .env

# Executar migrações
uv run python manage.py migrate
```

### 3. Iniciar Servidor
```bash
uv run python manage.py runserver
```

Servidor rodando em: **http://localhost:8000**

## 🧪 Teste Rápido

### Opção 1: Navegador
Abra: http://localhost:8000/api/docs

### Opção 2: curl (Terminal)
```bash
# Health check
curl http://localhost:8000/api/health

# Listar formatos
curl http://localhost:8000/api/formats
```

### Opção 3: Python
```python
import requests

# Transcrever áudio
url = "http://localhost:8000/api/transcribe"
files = {'file': open('seu_audio.mp3', 'rb')}
data = {'language': 'pt'}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## 📱 Testando com Áudios Reais

### WhatsApp
1. Envie um áudio para si mesmo no WhatsApp
2. Baixe o arquivo (.opus ou .ogg)
3. Transcreva:
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@whatsapp_audio.opus" \
  -F "language=pt"
```

### Instagram
1. Baixe um vídeo do Instagram
2. A API extrairá o áudio automaticamente:
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@instagram_video.mp4" \
  -F "language=pt"
```

## 🎯 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/health` | GET | Status da API |
| `/api/formats` | GET | Formatos suportados |
| `/api/transcribe` | POST | Transcrever áudio |
| `/api/transcribe/batch` | POST | Múltiplos arquivos |
| `/api/docs` | GET | Documentação Swagger |

## ⚙️ Configuração Rápida

### Arquivo `.env`:
```env
# Modelo Whisper: tiny, base, small, medium, large
WHISPER_MODEL=medium

# Tamanho máximo (MB)
MAX_AUDIO_SIZE_MB=25

# Diretório temporário
TEMP_AUDIO_DIR=/tmp/daredevil
```

### Escolher Modelo:
- **tiny**: Muito rápido, qualidade básica
- **base**: Rápido, boa qualidade
- **small**: Moderado, muito boa qualidade
- **medium**: ⭐ **Recomendado** - Melhor equilíbrio
- **large**: Lento, melhor qualidade

## 🔥 Exemplos Práticos

### 1. Transcrição Simples
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt"
```

### 2. Com Modelo Específico
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.wav" \
  -F "language=pt" \
  -F "model=large"
```

### 3. Script Python
```python
import requests

def transcrever(arquivo, idioma="pt"):
    url = "http://localhost:8000/api/transcribe"
    files = {'file': open(arquivo, 'rb')}
    data = {'language': idioma}
    
    response = requests.post(url, files=files, data=data)
    result = response.json()
    
    if result['success']:
        print(f"Transcrição: {result['transcription']['text']}")
        print(f"Tempo: {result['processing_time']}s")
    else:
        print(f"Erro: {result['error']}")

# Usar
transcrever("meu_audio.mp3")
```

## 🐛 Problemas Comuns

### "Connection refused"
- Servidor não está rodando
- Solução: `uv run python manage.py runserver`

### "File format not supported"
- Formato inválido
- Solução: Verificar formatos com `curl http://localhost:8000/api/formats`

### "File too large"
- Arquivo maior que 25MB
- Solução: Aumentar `MAX_AUDIO_SIZE_MB` no `.env`

### Transcrição muito lenta
- Modelo muito grande para CPU
- Solução: Usar modelo menor (`WHISPER_MODEL=small`)

## 📊 Resposta Esperada

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

## 🎓 Próximos Passos

1. **Explorar a documentação**: http://localhost:8000/api/docs
2. **Testar diferentes formatos**: WhatsApp, Instagram, etc
3. **Ajustar modelo**: Testar `tiny`, `small`, `medium`, `large`
4. **Processamento em lote**: Use `/api/transcribe/batch`
5. **Integração**: Use a API em seus projetos

## 📞 Suporte

- 📖 **Documentação completa**: README.md
- 🔧 **Requisitos do sistema**: REQUIREMENTS.md
- 💡 **Exemplos**: examples.py
- 🐛 **Issues**: GitHub Issues

---

**Pronto para começar?** 🚀

```bash
uv run python manage.py runserver
```

Então acesse: http://localhost:8000/api/docs
