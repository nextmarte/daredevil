# GitHub Copilot Instructions - Daredevil API

## Visão Geral do Projeto
API de transcrição de áudio em português usando Django Ninja, focada em alta qualidade e suporte a múltiplos formatos de áudio.

## Stack Tecnológica
- **Gerenciamento de Ambiente**: uv (gerenciador de pacotes Python ultrarrápido)
- **Framework**: Django + Django Ninja API
- **Transcrição**: Whisper (OpenAI) - modelo otimizado para português
- **Processamento de Áudio**: pydub, ffmpeg
- **Validação**: pydantic (integrado com Django Ninja)
- **Armazenamento**: Sistema de arquivos local (temporário)

## Formatos de Áudio Suportados
- **WhatsApp**: .opus, .ogg, .m4a, .aac
- **Instagram**: .mp4, .m4a, .aac
- **Padrão**: .wav, .mp3, .flac, .webm
- **Limite de tamanho**: 25MB por arquivo

## Estrutura da API

### Endpoints
```
POST /api/transcribe
- Aceita upload de arquivo de áudio
- Retorna transcrição detalhada com timestamps
- Suporta parâmetros: language=pt, model=medium/large

GET /api/health
- Status da API e modelos carregados

POST /api/transcribe/batch
- Processa múltiplos arquivos simultaneamente
```

### Modelo de Resposta
```python
{
    "success": bool,
    "transcription": {
        "text": str,  # Texto completo
        "segments": [  # Segmentos com timestamps
            {
                "start": float,
                "end": float,
                "text": str,
                "confidence": float
            }
        ],
        "language": str,
        "duration": float
    },
    "processing_time": float,
    "audio_info": {
        "format": str,
        "duration": float,
        "sample_rate": int,
        "channels": int
    }
}
```

## Boas Práticas de Código

### Processamento de Áudio
- Sempre converter áudio para formato compatível (wav/mp3)
- Normalizar sample rate para 16kHz (otimizado para Whisper)
- Limpar arquivos temporários após processamento
- Validar integridade do arquivo antes de processar
- Implementar timeout para processamentos longos

### Segurança
- Validar tipo MIME do arquivo
- Limitar tamanho máximo de upload
- Sanitizar nomes de arquivos
- Usar storage temporário seguro
- Implementar rate limiting

### Performance
- Processar áudios de forma assíncrona quando possível
- Usar modelo Whisper adequado (base/small para rapidez, medium/large para qualidade)
- Implementar cache para áudios já processados (hash do arquivo)
- Otimizar conversão de áudio (usar ffmpeg diretamente)

### Tratamento de Erros
- Erros de formato de áudio inválido
- Timeout em processamentos longos
- Arquivo corrompido ou vazio
- Modelo de transcrição não disponível
- Memória insuficiente

## Otimizações para Português
- Usar modelo Whisper com language='pt'
- Considerar fine-tuning para sotaques brasileiros
- Implementar pós-processamento de texto:
  - Correção de pontuação
  - Capitalização adequada
  - Remoção de hesitações comuns

## Conversões de Formato Específicas

### WhatsApp (.opus, .ogg)
```python
# Converter de opus para wav
ffmpeg -i input.opus -ar 16000 -ac 1 output.wav
```

### Instagram (.mp4 com áudio)
```python
# Extrair áudio de vídeo
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 output.wav
```

## Testes
- Testar com áudios de diferentes durações (5s a 10min)
- Testar todos os formatos suportados
- Testar com ruído de fundo
- Testar com múltiplos falantes
- Testar áudios do WhatsApp e Instagram reais

## Logging e Monitoramento
- Log de tempo de processamento por áudio
- Log de formato e tamanho de arquivo
- Log de erros de conversão
- Métricas de qualidade da transcrição (quando possível)

## Dependências Principais
```toml
# Instalar com: uv add <package>
dependencies = [
    "django>=4.2",
    "django-ninja>=1.0",
    "openai-whisper",
    "pydub",
    "python-multipart",  # Para upload de arquivos
    "ffmpeg-python",
]
```

## Comandos uv Comuns
```bash
# Adicionar dependência
uv add django django-ninja openai-whisper pydub python-multipart ffmpeg-python

# Sincronizar ambiente
uv sync

# Executar comando no ambiente
uv run python manage.py runserver

# Executar shell Python
uv run python

# Ativar ambiente virtual (se necessário)
source .venv/bin/activate
```

## Variáveis de Ambiente
```
WHISPER_MODEL=medium  # base, small, medium, large
MAX_AUDIO_SIZE_MB=25
TEMP_AUDIO_DIR=/tmp/daredevil
ENABLE_CACHE=true
LOG_LEVEL=INFO
```

## Notas de Implementação
1. **Setup inicial**: `uv sync` para criar ambiente e instalar dependências
2. Instalar ffmpeg no sistema: `apt-get install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS)
3. Whisper será baixado automaticamente na primeira execução (~1-3GB dependendo do modelo)
4. Modelos maiores requerem mais memória RAM (large ~10GB)
5. Considerar usar GPU para processamento mais rápido (CUDA)
6. Usar `uv run` para executar comandos no ambiente gerenciado
