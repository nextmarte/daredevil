# 🚀 QUICK START - Testar Suporte a Vídeos

## ⚡ Em 5 Minutos

### 1️⃣ Iniciar o Container

```bash
cd /home/marcus/projects/daredevil
docker compose up -d
```

Aguarde ~30 segundos para o container estar pronto.

### 2️⃣ Verificar Status

```bash
# Verificar se API está respondendo
curl http://localhost:8511/api/health

# Deve retornar:
# {
#   "status": "healthy",
#   "whisper_model": "medium",
#   "max_file_size_mb": 500,
#   ...
# }
```

### 3️⃣ Listar Formatos Suportados

```bash
curl http://localhost:8511/api/formats

# Resposta mostra todos os 12 formatos de vídeo + 9 de áudio
```

### 4️⃣ Testar com Vídeo Real

**Opção A: Criar vídeo de teste**
```bash
# Criar um vídeo de teste de 5 segundos (FFmpeg requerido)
ffmpeg -f lavfi -i color=c=blue:s=640x480:d=5 \
       -f lavfi -i sine=f=1000:d=5 \
       -pix_fmt yuv420p \
       -y test_video.mp4
```

**Opção B: Usar vídeo existente**
```bash
# Se tiver um vídeo qualquer
cp /caminho/seu_video.mp4 .
```

### 5️⃣ Enviar para Transcrição

```bash
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@test_video.mp4" \
  -F "language=pt"
```

**Resposta esperada:**
```json
{
  "success": true,
  "transcription": {
    "text": "...",
    "segments": [...]
  },
  "processing_time": 45.32,
  "audio_info": {
    "format": "mp4",
    "duration": 5.0,
    "sample_rate": 16000,
    "channels": 1
  }
}
```

---

## 📋 Testes Detalhados

### Teste 1: Validação de Formato

```bash
# Deve aceitar
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@video.mp4" \
  -F "language=pt"

# Deve rejeitar (formato inválido)
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@arquivo.txt"
```

### Teste 2: Limite de Tamanho

```bash
# Deve aceitar (< 500MB)
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@video_100mb.mp4"

# Deve rejeitar (> 500MB) com erro descritivo
```

### Teste 3: Validação de Vídeo

```bash
# Vídeo válido - OK
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@video_ok.mp4"

# Vídeo corrompido - ERRO
# (Retorna erro descritivo sobre integridade)
```

### Teste 4: Tipos de Vídeo

```bash
# Testar diferentes formatos
for format in mp4 avi mov mkv webm; do
  echo "Testando $format..."
  curl -X POST http://localhost:8511/api/transcribe \
    -F "file=@video.$format" \
    -F "language=pt"
done
```

### Teste 5: Processamento em Batch

```bash
# Múltiplos vídeos
curl -X POST http://localhost:8511/api/transcribe/batch \
  -F "files=@video1.mp4" \
  -F "files=@video2.mov" \
  -F "files=@video3.mkv"
```

---

## 🧪 Suite de Testes Automática

### Dentro do Container

```bash
# Executar todos os testes
docker compose exec daredevil uv run python test_video_support.py

# Deve mostrar:
# ✓ Sintaxe Python
# ✓ GPU Status
# ✓ MediaTypeDetector
# ✓ Formatos Suportados
# ✓ Validação de Vídeo
# ✓ Extração de Áudio
# ✓ Transcrição Completa
```

---

## 🐛 Debugging

### Ver Logs

```bash
# Em tempo real
docker compose logs -f daredevil

# Últimas 50 linhas
docker compose logs --tail=50 daredevil

# Apenas erros
docker compose logs daredevil | grep -i error
```

### Entrar no Container

```bash
docker compose exec daredevil bash

# Dentro do container:
# Listar formatos suportados
uv run python -c "from django.conf import settings; print(settings.ALL_SUPPORTED_FORMATS)"

# Testar VideoProcessor
uv run python -c "from transcription.video_processor import VideoProcessor; print('VideoProcessor OK')"

# Verificar ffmpeg
ffmpeg -version
ffprobe -version
```

### Validar Vídeo com FFprobe

```bash
# Dentro do container:
docker compose exec daredevil \
  ffprobe -v error -show_format -of json seu_video.mp4
```

---

## ✅ Checklist de Teste

- [ ] Container iniciado com sucesso
- [ ] API responde em `/api/health`
- [ ] Formatos listados em `/api/formats`
- [ ] Vídeo MP4 aceito
- [ ] Vídeo com outro formato aceito
- [ ] Transcrição completa com sucesso
- [ ] Resultado em português
- [ ] Tempos de processamento razoáveis
- [ ] GPU detectada e em uso
- [ ] Sem erros nos logs

---

## 🚨 Solução de Problemas

### Problema: "Connection refused"

```bash
# Container não está rodando
docker compose ps

# Se não aparecer, iniciar:
docker compose up -d

# Esperar ~30s e tentar novamente
sleep 30
curl http://localhost:8511/api/health
```

### Problema: "Arquivo de vídeo inválido"

```bash
# Validar vídeo com ffprobe (local)
ffprobe seu_video.mp4

# Converter se necessário
ffmpeg -i video.avi -c:v libx264 -c:a aac video.mp4

# Tentar novamente
```

### Problema: "Formato não suportado"

```bash
# Verificar formato aceito
curl http://localhost:8511/api/formats | grep -i mp4

# Se não aparecer, converter:
ffmpeg -i video.xyz -c:v libx264 -c:a aac output.mp4
```

### Problema: "Arquivo muito grande"

```bash
# Comprimir vídeo
ffmpeg -i input.mp4 -crf 28 output.mp4

# Ou extrair apenas audio
ffmpeg -i input.mp4 -vn -acodec libmp3lame audio.mp3
```

### Problema: GPU não detectada

```bash
# Verificar GPU dentro do container
docker compose exec daredevil nvidia-smi

# Ou chamar endpoint
curl http://localhost:8511/api/gpu-status
```

---

## 📊 Performance Esperada

### Primeira Execução
- Vai demorar um pouco (Whisper sendo carregado)
- ~60-90 segundos para 1 minuto de vídeo

### Execuções Subsequentes
- Modelo já em memória GPU
- ~15-20 segundos por minuto de vídeo
- Com GPU: 6-10x mais rápido que CPU

---

## 🎬 Exemplo Completo

```bash
#!/bin/bash

# 1. Iniciar container
echo "🚀 Iniciando container..."
docker compose up -d
sleep 30

# 2. Criar vídeo de teste
echo "🎥 Criando vídeo de teste..."
ffmpeg -f lavfi -i color=c=blue:s=640x480:d=10 \
       -f lavfi -i sine=f=1000:d=10 \
       -pix_fmt yuv420p -y test.mp4

# 3. Testar API
echo "📡 Testando API..."
curl http://localhost:8511/api/health

# 4. Listar formatos
echo "📋 Formatos suportados:"
curl http://localhost:8511/api/formats

# 5. Transcrever vídeo
echo "🎙️ Transcrevendo vídeo..."
time curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@test.mp4" \
  -F "language=pt"

# 6. Verificar GPU
echo "💾 Status da GPU:"
curl http://localhost:8511/api/gpu-status

echo "✅ Teste completo!"
```

---

## 📚 Documentação Completa

- **VIDEO_SUPPORT.md** - Guia detalhado de uso
- **VIDEO_IMPLEMENTATION.md** - Detalhes técnicos
- **test_video_support.py** - Suite de testes
- **check_video_implementation.py** - Verificador de estrutura

---

## 🎯 Próximos Passos

1. ✅ Iniciar container
2. ✅ Testar endpoints básicos
3. ✅ Enviar vídeo para transcrição
4. ✅ Verificar resultado em português
5. ✅ Monitorar performance com GPU
6. 🔄 Integrar com seu sistema
7. 🔄 Escalar conforme necessário

---

## 💡 Dicas

- Use modelo `medium` para bom balanço qualidade/velocidade
- Vídeos em português funcionam melhor (treinamento Whisper)
- GPU reduz tempo em 6-10x
- Máximo 500MB por arquivo
- Pós-processamento português é automático

---

## 📞 Comandos Úteis

```bash
# Status do container
docker compose ps

# Logs em tempo real
docker compose logs -f daredevil

# Entrar no shell
docker compose exec daredevil bash

# Parar container
docker compose stop

# Reiniciar container
docker compose restart

# Limpar tudo
docker compose down -v
```

---

Pronto para testar! 🎉

**Comece com**: `docker compose up -d` e `curl http://localhost:8511/api/health`
