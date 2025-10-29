# GitHub Copilot Instructions - Daredevil API

## Visão Geral do Projeto
API completa de transcrição de áudio e vídeo em português brasileiro usando Django Ninja, focada em alta qualidade e suporte a múltiplos formatos de áudio e vídeo, com aceleração por GPU NVIDIA.

## Stack Tecnológica
- **Gerenciamento de Ambiente**: uv (gerenciador de pacotes Python ultrarrápido)
- **Framework**: Django 5.2+ + Django Ninja API
- **Transcrição**: Whisper (OpenAI) - modelo otimizado para português brasileiro
- **Processamento de Áudio/Vídeo**: pydub, ffmpeg, ffprobe
- **GPU**: PyTorch com CUDA 12.1 (NVIDIA)
- **Validação**: pydantic (integrado com Django Ninja)
- **Armazenamento**: Sistema de arquivos local (temporário)
- **Containerização**: Docker + Docker Compose com suporte a GPU

## Formatos Suportados

### Áudio (9 formatos)
- **WhatsApp**: .opus, .ogg
- **Padrão**: .mp3, .wav, .flac, .aac, .m4a, .webm, .weba

### Vídeo (14 formatos)
- **Redes Sociais**: .mp4 (WhatsApp, Instagram, TikTok), .mov (iPhone)
- **Streaming**: .mkv, .webm, .flv, .ts, .m2ts, .mts
- **Legados**: .avi, .wmv, .ogv, .3gp, .f4v, .asf

### Limites
- **Tamanho máximo**: 500MB por arquivo (configurável)
- **Processamento**: Extração automática de áudio de vídeos

## Estrutura da API

### Endpoints
```
POST /api/transcribe
- Aceita upload de arquivo de áudio ou vídeo
- Extrai automaticamente áudio de vídeos usando ffmpeg
- Retorna transcrição detalhada com timestamps
- Suporta parâmetros: language=pt (padrão), model=medium/large

GET /api/health
- Status da API, modelos carregados, GPU status

GET /api/gpu-status
- Informações detalhadas sobre GPU(s) NVIDIA disponíveis
- Memória, capacidade de computação, etc.

GET /api/formats
- Lista todos os formatos de áudio e vídeo suportados
- Limite de tamanho de arquivo

POST /api/transcribe/batch
- Processa múltiplos arquivos de áudio/vídeo simultaneamente
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

### GPU e Performance
- Detectar automaticamente GPU disponível (torch.cuda.is_available())
- Usar GPU quando disponível para acelerar transcrição (5-10x mais rápido)
- Usar FP16 em GPU para economizar memória (~50% economia)
- Log de informações de GPU (nome, memória, capacidade de computação)
- Fallback gracioso para CPU se GPU não disponível
- Monitorar uso de memória GPU durante processamento
- Cache de modelos Whisper em memória GPU

### Processamento de Áudio e Vídeo
- **Vídeos**: Detectar formato de vídeo e extrair áudio automaticamente com ffmpeg
- **Validação**: Usar ffprobe para validar integridade de vídeos antes de processar
- **Conversão**: Sempre converter para WAV 16kHz mono PCM (otimizado para Whisper)
- **Limpeza**: Remover arquivos temporários WAV após processamento
- **Timeout**: Implementar timeout de 30 minutos para vídeos longos
- Normalizar sample rate para 16kHz (otimizado para Whisper)
- Limpar arquivos temporários após processamento
- Validar integridade do arquivo antes de processar
- Implementar timeout para processamentos longos

### Segurança
- Validar tipo MIME do arquivo
- Limitar tamanho máximo de upload (500MB padrão)
- Sanitizar nomes de arquivos
- Usar storage temporário seguro (/tmp/daredevil)
- Implementar rate limiting
- Validar integridade de vídeos com ffprobe

### Performance
- Processar áudios de forma assíncrona quando possível
- Usar modelo Whisper adequado:
  - CPU: base/small
  - GPU: medium/large para melhor qualidade
- Implementar cache para áudios já processados (hash do arquivo)
- Otimizar conversão de áudio/vídeo (usar ffmpeg diretamente)
- Processar vídeos: extrair áudio primeiro, depois transcrever
- Usar FP16 em GPU para economizar memória

### Tratamento de Erros
- Erros de formato de áudio/vídeo inválido
- Timeout em processamentos longos (vídeos grandes)
- Arquivo corrompido ou vazio
- Vídeo sem faixa de áudio
- Modelo de transcrição não disponível
- Memória insuficiente (GPU/CPU)
- GPU out of memory (usar modelo menor)

## Otimizações para Português Brasileiro
- **Idioma padrão**: language='pt' (não precisa especificar)
- **Pós-processamento automático** de texto em português:
  - Remoção de hesitações comuns (tipo, sabe, entendeu, né, hã, tá, etc.)
  - Normalização de pontuação (espaços antes/depois)
  - Capitalização adequada (início de frases, nomes próprios)
  - Expansão de abreviações (sr → Sr., ltda → Ltda., dr → Dr., etc.)
  - Correção de erros comuns (contrações, crase)
- **Módulo dedicado**: `transcription/portuguese_processor.py`
  - `PortugueseBRTextProcessor` class
  - `LanguageDetector` class
- **Locale**: pt_BR.UTF-8 configurado no sistema

## Processamento de Vídeos

### Fluxo de Processamento
1. **Detecção**: Identificar se arquivo é vídeo pela extensão
2. **Validação**: Usar ffprobe para verificar integridade
3. **Extração**: Converter vídeo para WAV 16kHz mono com ffmpeg
4. **Transcrição**: Processar áudio extraído com Whisper
5. **Pós-processamento**: Aplicar processamento de português
6. **Limpeza**: Remover arquivos temporários WAV

### Comandos FFmpeg
```bash
# Validação de vídeo
ffprobe -v error -show_format -show_streams -of json video.mp4

# Extração de áudio (otimizada para Whisper)
ffmpeg -i video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav

# Parâmetros:
# -vn: Remove vídeo (apenas áudio)
# -acodec pcm_s16le: PCM 16-bit
# -ar 16000: Sample rate 16kHz
# -ac 1: Mono (1 canal)
```

### Módulo VideoProcessor
- **Arquivo**: `transcription/video_processor.py`
- **Classes**:
  - `VideoProcessor`: Validação, extração, metadados
  - `MediaTypeDetector`: Detecção de tipo (áudio/vídeo/desconhecido)
- **Métodos principais**:
  - `validate_video_file()`: Valida integridade com ffprobe
  - `get_video_info()`: Extrai metadados (duração, codec, resolução)
  - `extract_audio()`: Extrai áudio para WAV 16kHz mono
  - `detect_media_type()`: Classifica arquivo por extensão

## Testes
- Testar com áudios de diferentes durações (5s a 10min)
- Testar todos os formatos de áudio suportados (9 formatos)
- **Testar formatos de vídeo** (14 formatos: mp4, avi, mov, mkv, etc.)
- **Testar extração de áudio de vídeos**
- Testar com ruído de fundo
- Testar com múltiplos falantes
- Testar áudios do WhatsApp (.opus, .ogg)
- Testar vídeos do Instagram, TikTok, iPhone (.mp4, .mov)
- **Testar GPU**: Verificar aceleração e uso de memória
- **Testar português**: Validar pós-processamento de texto
- **Testar batch**: Múltiplos arquivos (áudio + vídeo)

## Logging e Monitoramento
- Log de tempo de processamento por áudio/vídeo
- Log de formato e tamanho de arquivo
- Log de tipo de mídia (áudio vs vídeo)
- Log de erros de conversão (áudio e vídeo)
- **Log de uso de GPU** (memória alocada, tempo de processamento)
- **Log de extração de vídeo** (duração, codec, resolução)
- Métricas de qualidade da transcrição (quando possível)
- **Log de pós-processamento** de português (hesitações removidas, etc.)

## Dependências Principais
```toml
# Instalar com: uv add <package>
dependencies = [
    "django>=5.2",
    "django-ninja>=1.0",
    "openai-whisper",
    "torch",  # PyTorch com CUDA
    "pydub",
    "python-multipart",  # Para upload de arquivos
    "ffmpeg-python",
    "numpy",
]

# GPU (opcional mas recomendado)
# torch com CUDA: --index-url https://download.pytorch.org/whl/cu121
```

## Comandos uv Comuns
```bash
# Adicionar dependência
uv add django django-ninja openai-whisper pydub python-multipart ffmpeg-python

# Sincronizar ambiente
uv sync

# Executar comando no ambiente (SEMPRE usar uv run)
uv run python manage.py runserver

# Executar qualquer script Python
uv run python script.py

# Executar shell Python
uv run python

# Ver versão do UV
uv --version

# IMPORTANTE: NO DOCKER, sempre usar 'uv run' antes de qualquer comando Python
# Exemplo: uv run python manage.py migrate
```

## Docker e UV
**CRÍTICO**: No ambiente Docker, o UV gerencia um ambiente virtual isolado. Portanto:
- ✅ **SEMPRE** usar `uv run python manage.py <comando>`
- ✅ **SEMPRE** usar `uv run python script.py`
- ❌ **NUNCA** usar apenas `python manage.py <comando>` (não encontrará os pacotes)
- ❌ **NUNCA** usar `pip install` (usar `uv add` em vez disso)

O `docker-entrypoint.sh` deve executar:
```bash
uv sync                                    # Instala dependências
uv run python manage.py migrate           # Usa ambiente do UV
uv run python manage.py runserver         # Usa ambiente do UV
```

## Variáveis de Ambiente
```
# Modelo Whisper
WHISPER_MODEL=medium  # tiny, base, small, medium, large
WHISPER_LANGUAGE=pt   # Português brasileiro como padrão

# Limites
MAX_AUDIO_SIZE_MB=500  # Aumentado de 25MB para 500MB
TEMP_AUDIO_DIR=/tmp/daredevil

# Cache e logs
ENABLE_CACHE=true
LOG_LEVEL=INFO

# Django
DEBUG=0
ALLOWED_HOSTS=*
SECRET_KEY=your-secret-key

# Locale (Português Brasileiro)
LANGUAGE=pt_BR.UTF-8
LANG=pt_BR.UTF-8
LC_ALL=pt_BR.UTF-8

# GPU (opcional)
CUDA_VISIBLE_DEVICES=0  # Especificar GPU se tiver múltiplas
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Otimizar memória
```

## Notas de Implementação
1. **Setup inicial**: `uv sync` para criar ambiente e instalar dependências
2. **FFmpeg obrigatório**: Instalar no sistema - `apt-get install ffmpeg` (Linux) ou `brew install ffmpeg` (macOS)
3. **Whisper**: Será baixado automaticamente na primeira execução (~1-3GB dependendo do modelo)
4. **GPU NVIDIA (opcional mas recomendado)**:
   - Instalar CUDA Toolkit 12.1+
   - Instalar PyTorch com CUDA: `uv add torch --index-url https://download.pytorch.org/whl/cu121`
   - No Docker: NVIDIA Container Toolkit necessário
   - Dockerfile usa `nvidia/cuda:12.1.0-base-ubuntu22.04` como base
5. **Modelos maiores**: Requerem mais memória (large ~10GB RAM ou 10GB VRAM)
6. **Usar `uv run`**: Sempre executar comandos com `uv run python ...` no ambiente gerenciado
7. **Português brasileiro**: Pós-processamento automático ativo por padrão
8. **Vídeos**: Extração de áudio automática com ffmpeg para todos os 14 formatos suportados

## Performance Esperada

### Com CPU (Intel i5 8 cores)
- **tiny**: ~30s por minuto de áudio
- **base**: ~45s por minuto de áudio
- **small**: ~60s por minuto de áudio
- **medium**: ~90s por minuto de áudio (não recomendado)

### Com GPU (NVIDIA RTX 3060)
- **tiny**: ~3-5s por minuto de áudio (10x mais rápido)
- **base**: ~5-8s por minuto de áudio
- **small**: ~8-12s por minuto de áudio
- **medium**: ~12-18s por minuto de áudio (⭐ recomendado)
- **large**: ~18-25s por minuto de áudio

### Vídeos (com GPU RTX 3060)
- **1 minuto**: ~15-20 segundos
- **5 minutos**: ~30-40 segundos
- **30 minutos**: ~2-3 minutos
- **1 hora**: ~4-6 minutos

## Estrutura de Arquivos Importantes

```
daredevil/
├── config/
│   ├── settings.py              # SUPPORTED_VIDEO_FORMATS, ALL_SUPPORTED_FORMATS
│   └── urls.py
├── transcription/
│   ├── api.py                   # Endpoints: /transcribe, /health, /gpu-status, /formats
│   ├── services.py              # TranscriptionService, WhisperTranscriber
│   ├── audio_processor.py       # AudioProcessor class
│   ├── video_processor.py       # VideoProcessor, MediaTypeDetector (NOVO)
│   ├── portuguese_processor.py  # PortugueseBRTextProcessor (NOVO)
│   └── schemas.py               # Pydantic models
├── Dockerfile                   # nvidia/cuda:12.1.0-base-ubuntu22.04
├── docker-compose.yml           # GPU support configurado
├── docker-entrypoint.sh         # uv sync + migrate + runserver
├── test_gpu.py                  # Testar GPU
├── test_portuguese_br.py        # Testar português
├── test_video_support.py        # Testar vídeos (NOVO)
└── README.md                    # Documentação completa consolidada
```

## Recursos Principais Implementados

### ✅ GPU NVIDIA com CUDA 12.1
- Detecção automática de GPU
- FP16 para economia de memória
- Fallback para CPU
- Endpoint `/api/gpu-status`
- Performance 5-10x mais rápida

### ✅ Português Brasileiro
- Idioma padrão (não precisa especificar)
- Pós-processamento automático:
  - Remoção de hesitações (tipo, sabe, né, etc.)
  - Normalização de pontuação
  - Capitalização correta
  - Expansão de abreviações (sr → Sr., ltda → Ltda.)
- Locale pt_BR.UTF-8

### ✅ Suporte a Vídeos (14 formatos)
- Detecção automática de vídeo vs áudio
- Validação com ffprobe
- Extração de áudio com ffmpeg (16kHz mono WAV)
- Limpeza automática de temporários
- Suporte: mp4, avi, mov, mkv, flv, wmv, webm, ogv, ts, mts, m2ts, 3gp, f4v, asf

### ✅ Limite de 500MB
- Aumentado de 25MB para 500MB
- Configurável via MAX_AUDIO_SIZE_MB
- Suporta vídeos longos (até ~2-3 horas)

### ✅ API REST Completa
- `/api/transcribe` - Transcrição de áudio/vídeo
- `/api/transcribe/batch` - Processamento em lote
- `/api/health` - Status da API
- `/api/gpu-status` - Status da GPU
- `/api/formats` - Formatos suportados
- `/api/docs` - Documentação Swagger
- `/api/redoc` - Documentação ReDoc
