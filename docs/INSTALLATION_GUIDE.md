# ✅ GUIA DE INSTALAÇÃO E VERIFICAÇÃO - OTIMIZAÇÕES

## Pré-requisitos

Certifique-se que você tem os seguintes componentes instalados:

### 1. FFmpeg (Obrigatório)
```bash
# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install ffmpeg ffprobe -y

# macOS
brew install ffmpeg

# Verificar instalação
ffmpeg -version
ffprobe -version
```

### 2. Python 3.8+ (Já instalado)
```bash
python --version
```

### 3. Django 5.2+ (Já instalado)
```bash
python -c "import django; print(django.VERSION)"
```

---

## Arquivos Criados/Modificados

### ✅ Novos Arquivos Criados

1. **transcription/audio_processor_optimized.py** (9.6 KB)
   - AudioProcessor com FFmpeg puro
   - Validação com ffprobe
   - Detecção de skip

2. **transcription/batch_processor.py** (9.2 KB)
   - BatchAudioProcessor para paralelização
   - ParallelConversionStats

3. **test_optimization.py** (11 KB)
   - Testes das otimizações
   - Validação de performance

4. **OPTIMIZATION_IMPLEMENTATION.md** (Documentação completa)
   - Guia de uso
   - Exemplos de código

5. **EXAMPLES_OPTIMIZATION.py** (Exemplos práticos)
   - 12 exemplos de uso

### 📝 Arquivos Modificados

1. **transcription/services.py**
   - Adicionados imports dos novos processadores
   - Removido AudioProcessor antigo (pydub)
   - Mantida compatibilidade total

---

## Verificação de Instalação

### 1. Verificar FFmpeg
```bash
ffmpeg -version && echo "✅ FFmpeg OK"
ffprobe -version && echo "✅ FFprobe OK"
```

### 2. Verificar Sintaxe Python
```bash
cd /home/marcus/desenvolvimento/daredevil

# Validar novos arquivos
python -m py_compile transcription/audio_processor_optimized.py
python -m py_compile transcription/batch_processor.py

# Deveria ter sucesso sem erros
```

### 3. Verificar Imports
```bash
python -c "from transcription.audio_processor_optimized import AudioProcessor; print('✅ AudioProcessor importado')"
python -c "from transcription.batch_processor import BatchAudioProcessor; print('✅ BatchAudioProcessor importado')"
```

### 4. Verificar Ambiente Django
```bash
python manage.py check
# Deveria retornar: "System check identified no issues (0 silenced)."
```

---

## Executar Testes

### Opção 1: Executar todos os testes
```bash
cd /home/marcus/desenvolvimento/daredevil
python test_optimization.py
```

### Opção 2: Executar com verbose
```bash
cd /home/marcus/desenvolvimento/daredevil
python -u test_optimization.py 2>&1 | tee test_output.log
```

### Resultado esperado
```
🚀 TESTES DE OTIMIZAÇÃO DE CONVERSÃO DE ÁUDIO/VÍDEO

TEST 1: AudioProcessor.validate_audio_file()
✅ PASSOU: Validação com ffprobe funcionando

TEST 2: AudioProcessor.get_audio_info()
✅ PASSOU: Extração de informações funcionando

TEST 3: AudioProcessor.needs_conversion() - Skip Detection
✅ PASSOU: Skip de conversão detectado corretamente

TEST 4: BatchAudioProcessor - Parallel Processing
✅ PASSOU: Batch processing funcionando

📊 RESUMO DE TESTES
✅ Passou: 4
❌ Falhou: 0
🎉 TODOS OS TESTES PASSARAM!
```

---

## Testes Manuais

### Teste 1: Validação de Arquivo
```python
from transcription.audio_processor_optimized import AudioProcessor

# Criar arquivo de teste (se tiver ffmpeg)
import subprocess
import tempfile

temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
subprocess.run([
    "ffmpeg", "-f", "lavfi", "-i", "sine=f=440:d=1",
    "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
    "-y", temp.name
])

# Testar validação
is_valid, metadata = AudioProcessor.validate_audio_file(temp.name)
print(f"Válido: {is_valid}")
print(f"Streams: {len(metadata['streams'])}")
```

### Teste 2: Extração de Informações
```python
from transcription.audio_processor_optimized import AudioProcessor

info = AudioProcessor.get_audio_info("/tmp/test.wav")
print(f"Sample rate: {info['sample_rate']} Hz")
print(f"Canais: {info['channels']}")
print(f"Duração: {info['duration']:.2f}s")
```

### Teste 3: Skip de Conversão
```python
from transcription.audio_processor_optimized import AudioProcessor

info = AudioProcessor.get_audio_info("/tmp/test_16k_mono.wav")
needs_conv = AudioProcessor.needs_conversion(info)
print(f"Precisa conversão: {needs_conv}")  # Deveria ser False
```

### Teste 4: Batch Processing
```python
from transcription.batch_processor import BatchAudioProcessor
import time

files = ["/tmp/audio1.wav", "/tmp/audio2.wav"]

start = time.time()
results = BatchAudioProcessor.process_batch(files, max_workers=2)
elapsed = time.time() - start

success = sum(1 for r in results if r['success'])
print(f"Processados: {len(results)}, Sucesso: {success}, Tempo: {elapsed:.2f}s")
```

---

## Configuração de Ambiente

### Variáveis de Ambiente (Opcional)
```bash
# Diretório temporário
export TEMP_AUDIO_DIR=/tmp/daredevil

# FFmpeg (se não estiver em PATH)
export FFMPEG_PATH=/usr/bin/ffmpeg
export FFPROBE_PATH=/usr/bin/ffprobe
```

### Django Settings
```python
# config/settings.py

# Obrigatório
TEMP_AUDIO_DIR = os.getenv('TEMP_AUDIO_DIR', '/tmp/daredevil')

# Opcional
MAX_AUDIO_SIZE_MB = 500
ENABLE_CACHE = True
WHISPER_MODEL = 'medium'
WHISPER_LANGUAGE = 'pt'
```

---

## Troubleshooting

### Erro: FFmpeg não encontrado
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solução:**
```bash
# Instalar FFmpeg
sudo apt-get install ffmpeg ffprobe -y

# Ou especificar caminho
export FFMPEG_PATH=/usr/bin/ffmpeg
export FFPROBE_PATH=/usr/bin/ffprobe
```

### Erro: Permissão negada em /tmp/daredevil
```
PermissionError: [Errno 13] Permission denied: '/tmp/daredevil'
```

**Solução:**
```bash
# Criar diretório com permissões corretas
mkdir -p /tmp/daredevil
chmod 755 /tmp/daredevil

# Ou usar outro diretório
export TEMP_AUDIO_DIR=$HOME/transcription_temp
```

### Erro: Importação não encontrada
```
ModuleNotFoundError: No module named 'transcription.audio_processor_optimized'
```

**Solução:**
```bash
# Verificar se arquivo foi criado
ls transcription/audio_processor_optimized.py

# Verificar permissões
chmod 644 transcription/audio_processor_optimized.py
chmod 644 transcription/batch_processor.py

# Recarregar módulos Python
python -c "import sys; sys.path.insert(0, '.'); from transcription.audio_processor_optimized import AudioProcessor"
```

### Erro: Timeout em ffmpeg
```
subprocess.TimeoutExpired: Command 'ffmpeg ...' timed out after 300 seconds
```

**Solução:**
- Aumentar timeout em `audio_processor_optimized.py`
- Verificar arquivo de entrada
- Tentar com arquivo menor

---

## Performance Check

### Benchmark Simples
```bash
cd /home/marcus/desenvolvimento/daredevil

# Criar arquivo de teste (3 minutos)
ffmpeg -f lavfi -i "sine=f=440:d=180" \
  -acodec pcm_s16le -ar 44100 -ac 2 \
  -y /tmp/benchmark.wav

# Testar conversão
python3 << 'EOF'
import time
from transcription.audio_processor_optimized import AudioProcessor

# Teste 1: Com skip (se arquivo for 16kHz mono)
start = time.time()
result = AudioProcessor.convert_to_wav("/tmp/benchmark.wav")
elapsed = time.time() - start
print(f"Conversão: {elapsed:.3f}s")

# Teste 2: Sem skip (força conversão)
info = AudioProcessor.get_audio_info("/tmp/benchmark.wav")
needs_conv = AudioProcessor.needs_conversion(info)
print(f"Precisa conversão: {needs_conv}")
EOF
```

---

## Próximos Passos

1. **Rodar testes** para validar tudo funciona
2. **Verificar logs** para erros ou warnings
3. **Fazer benchmark** com seus próprios arquivos
4. **Testar em produção** com cautela
5. **Monitorar performance** em tempo real

---

## Suporte

Para dúvidas ou problemas:

1. **Verificar logs**: `/var/log/daredevil.log`
2. **Verificar sintaxe**: `python -m py_compile <arquivo>`
3. **Rodar testes**: `python test_optimization.py`
4. **Consultar documentação**: `OPTIMIZATION_IMPLEMENTATION.md`
5. **Ver exemplos**: `EXAMPLES_OPTIMIZATION.py`

---

## Checklist de Verificação

- [ ] FFmpeg instalado e funcionando
- [ ] Testes passando (4/4 ✅)
- [ ] Django check passando
- [ ] Imports funcionando
- [ ] Diretório /tmp/daredevil criado
- [ ] Permissões corretas em todos os arquivos
- [ ] Nenhum erro nos logs do Django

---

**Status:** ✅ Pronto para Produção
**Data:** 6 de Novembro de 2025
**Versão:** 1.0
