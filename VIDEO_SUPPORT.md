# 🎥 Suporte a Vídeos - Daredevil API

## Visão Geral

A Daredevil API agora suporta **upload e transcrição automática de arquivos de vídeo**. Quando um vídeo é enviado, o sistema automaticamente:

1. ✅ Valida a integridade do arquivo de vídeo
2. ✅ Extrai o áudio em qualidade otimizada (16kHz, mono, WAV)
3. ✅ Transcreve o áudio com Whisper
4. ✅ Aplica processamento de português brasileiro
5. ✅ Retorna transcrição com timestamps

## Formatos de Vídeo Suportados

| Extensão | Descrição | Uso Comum |
|----------|-----------|-----------|
| `.mp4` | MPEG-4 Video | WhatsApp, Instagram, padrão |
| `.avi` | Audio Video Interleave | Arquivos legados, Windows |
| `.mov` | QuickTime | iPhone, macOS |
| `.mkv` | Matroska | Vídeos em alta qualidade |
| `.flv` | Flash Video | YouTube antigo |
| `.wmv` | Windows Media Video | Windows Media Player |
| `.webm` | WebM | Web, HTML5 |
| `.ogv` | Ogg Video | Web aberto |
| `.ts` | MPEG Transport Stream | TV digital, streaming |
| `.mts` | MPEG Transport Stream (Sony) | Câmeras digitais |
| `.m2ts` | MPEG-2 Transport Stream | Blu-ray, câmeras HD |
| `.3gp` | 3GPP | Celulares antigos |
| `.f4v` | Flash Video | Adobe Flash |
| `.asf` | Advanced Systems Format | Windows Media |

## Limites e Restrições

- **Tamanho máximo**: 500 MB por arquivo
- **Duração**: Até ~10 horas (dependendo de bitrate)
- **Tempo de processamento**: Proporcionalmente maior que áudio
- **GPU**: Recomendada para vídeos longos (2x RTX 3060 disponível)

## Exemplos de Uso

### cURL - Vídeo Simples

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@video.mp4" \
  -F "language=pt"
```

### cURL - Vídeo com Modelo Grande

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@interview.mov" \
  -F "language=pt" \
  -F "model=large"
```

### Python - Usando requests

```python
import requests

with open('video.mp4', 'rb') as f:
    files = {'file': f}
    data = {'language': 'pt'}
    response = requests.post(
        'http://localhost:8511/api/transcribe',
        files=files,
        data=data
    )
    print(response.json())
```

### Python - Batch com vídeos

```python
import requests

files_list = []
with open('video1.mp4', 'rb') as f1, open('video2.mkv', 'rb') as f2:
    response = requests.post(
        'http://localhost:8511/api/transcribe/batch',
        files={'files': [f1, f2]},
        data={'language': 'pt'}
    )
    for result in response.json()['results']:
        print(f"Texto: {result['transcription']['text']}")
        print(f"Duração: {result['audio_info']['duration']}s")
```

## Resposta da API

```json
{
  "success": true,
  "transcription": {
    "text": "Olá, essa é uma transcrição de vídeo.",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Olá, essa é uma transcrição de vídeo.",
        "confidence": 0.95
      }
    ],
    "language": "pt",
    "duration": 2.5
  },
  "processing_time": 45.32,
  "audio_info": {
    "format": "mp4",
    "duration": 2.5,
    "sample_rate": 16000,
    "channels": 1,
    "file_size_mb": 5.25
  },
  "error": null
}
```

## Fluxo de Processamento

```
Arquivo Vídeo (mp4, mkv, mov, etc)
    ↓
[1. Validação] - Verificar integridade com ffprobe
    ↓
[2. Extração de Áudio] - FFmpeg → 16kHz mono WAV
    ↓
[3. Transcrição] - Whisper (GPU se disponível)
    ↓
[4. Pós-processamento] - Português brasileiro
    ↓
JSON Response com transcrição
```

## Tecnologia Subjacente

### FFmpeg (Extração de Áudio)

O sistema usa FFmpeg para extrair áudio do vídeo:

```bash
ffmpeg -i input.mp4 \
  -vn \
  -acodec pcm_s16le \
  -ar 16000 \
  -ac 1 \
  output.wav
```

**Parâmetros:**
- `-vn`: Remove vídeo (apenas áudio)
- `-acodec pcm_s16le`: Codificador PCM 16-bit
- `-ar 16000`: Taxa de amostragem (otimizada para Whisper)
- `-ac 1`: Mono (1 canal)

### FFprobe (Validação)

Antes de processar, o sistema valida o vídeo:

```bash
ffprobe -v error \
  -show_format \
  -show_streams \
  -of json \
  input.mp4
```

## Performance

### Tempos Típicos (RTX 3060)

| Tipo | Duração | Tempo Processamento |
|------|---------|-------------------|
| Vídeo curto | 1 minuto | ~15-20s |
| Vídeo médio | 5 minutos | ~30-40s |
| Vídeo longo | 30 minutos | ~2-3 minutos |
| Vídeo HD | 1 hora | ~4-6 minutos |

**Fatores que afetam:**
- Tamanho e resolução do vídeo
- Bitrate de áudio
- Modelo Whisper usado (base/small/medium/large)
- Disponibilidade de GPU
- Carga do sistema

## Tratamento de Erros

### Erro: Arquivo de vídeo inválido

```json
{
  "success": false,
  "error": "Arquivo de vídeo inválido ou corrompido",
  "audio_info": null
}
```

**Solução**: Verifique o arquivo com:
```bash
ffprobe -v error input.mp4
```

### Erro: Formato não suportado

```json
{
  "success": false,
  "error": "Formato 'xxx' não suportado. Formatos aceitos: ...",
  "audio_info": null
}
```

**Solução**: Converta para MP4 usando FFmpeg:
```bash
ffmpeg -i input.xyz -c:v libx264 -c:a aac output.mp4
```

### Erro: Arquivo muito grande

```json
{
  "success": false,
  "error": "Arquivo muito grande: 600.50MB (máximo: 500MB)"
}
```

**Solução**: Comprima o vídeo:
```bash
ffmpeg -i input.mp4 -crf 28 output.mp4
```

### Erro: Sem áudio no vídeo

```json
{
  "success": false,
  "error": "Erro ao extrair áudio: Nenhuma faixa de áudio encontrada"
}
```

**Solução**: Verifique se o vídeo tem áudio:
```bash
ffprobe -v error -select_streams a input.mp4
```

## Endpoints da API

### GET /api/formats

Lista todos os formatos suportados:

```bash
curl http://localhost:8511/api/formats
```

Resposta:
```json
{
  "audio_formats": ["aac", "m4a", "mp3", "ogg", "opus", "wav", ...],
  "video_formats": ["3gp", "asf", "avi", "f4v", "flv", "m2ts", "mkv", "mov", "mp4", ...],
  "all_formats": ["3gp", "aac", "asf", "avi", ...],
  "max_file_size_mb": 500
}
```

### GET /api/health

Verificar status da API:

```bash
curl http://localhost:8511/api/health
```

### GET /api/gpu-status

Verificar status das GPUs:

```bash
curl http://localhost:8511/api/gpu-status
```

## Instalação de Dependências

Todas as dependências já estão instaladas no container Docker:

```dockerfile
# Já incluído no Dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

### Instalação Local (desenvolvimento)

```bash
# Linux (Debian/Ubuntu)
sudo apt-get install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

## Otimizações de Português

O sistema aplica automaticamente:

1. **Remoção de hesitações**: Tipo, sabe, entendeu, né, hã, ahn, hã, etc.
2. **Normalização de pontuação**: Corrige espaços antes de pontos, vírgulas
3. **Capitalização**: Capitaliza primeiras palavras de frases
4. **Expansão de abreviações**: Sr → Sr., Ltda → Ltda., etc.
5. **Correção de erros comuns**: Crase, contrações, etc.

Exemplo:
```
Entrada (bruta do Whisper):
"tipo , sabe , eu gosto muito desse vídeo , entendeu ? né , é legal"

Saída (pós-processada):
"Tipo, sabe, eu gosto muito desse vídeo, entendeu? Né, é legal."
```

## Casos de Uso

### 1. Transcrição de Reuniões

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@meeting.mp4" \
  -F "model=large"
```

Ideal para: Reuniões em vídeo, webinars, apresentações

### 2. Transcrição de Conteúdo de Redes Sociais

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@tiktok_video.mp4" \
  -F "language=pt"
```

Ideal para: Instagram, TikTok, YouTube

### 3. Transcrição de Arquivos de TV/Streaming

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@episode.mkv" \
  -F "model=medium"
```

Ideal para: Episódios, filmes, séries

### 4. Processamento em Lote

```bash
curl -X POST http://localhost:8511/api/transcribe/batch \
  -F "files=@video1.mp4" \
  -F "files=@video2.mov" \
  -F "files=@video3.mkv"
```

Ideal para: Múltiplos vídeos, processamento automatizado

## Monitoramento e Logs

Verificar logs de processamento:

```bash
# Docker
docker-compose logs -f daredevil | grep -i video

# Ver log em tempo real
tail -f /var/log/daredevil/transcription.log
```

## Limpeza de Arquivos Temporários

Arquivos temporários são **automaticamente removidos** após processamento:

- Arquivos WAV extraídos de vídeos
- Logs de processamento (mantidos por 7 dias)
- Cache temporário

## Próximas Melhorias

- [ ] Suporte a extração de múltiplas faixas de áudio
- [ ] Processamento de streams em tempo real
- [ ] Detecção automática de idioma em vídeos
- [ ] Extração de legendas em tempo real
- [ ] Suporte a vídeos 360° e VR
- [ ] Integração com bancos de dados de vídeos

## Suporte e Debugging

### Verificar FFmpeg

```bash
# Verificar instalação
ffmpeg -version
ffprobe -version

# Dentro do container
docker exec daredevil ffmpeg -version
```

### Validar Vídeo

```bash
ffprobe -v error -show_format -show_streams -of json video.mp4
```

### Logs de Debug

```python
# Em services.py
logger.debug(f"Vídeo detectado: {extension}")
logger.debug(f"Extração iniciada: {video_info}")
logger.debug(f"Áudio extraído: {temp_wav_path}")
```

## Referências

- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Django File Upload](https://docs.djangoproject.com/en/stable/ref/request-response/#django.http.HttpRequest.FILES)

---

**Última atualização**: 2024
**Versão**: 1.0.0
