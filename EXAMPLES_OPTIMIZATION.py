"""
Exemplos práticos de como usar as otimizações implementadas.
"""

# ============================================================================
# EXEMPLO 1: Conversão simples de áudio
# ============================================================================

from transcription.services import TranscriptionService
from transcription.services import temporary_file
import logging
from transcription.services import WhisperTranscriber
from transcription.batch_processor import ParallelConversionStats
import time
from transcription.batch_processor import BatchAudioProcessor
from transcription.audio_processor_optimized import AudioProcessor

# Converter arquivo para WAV 16kHz mono
wav_path = AudioProcessor.convert_to_wav(
    input_path="/tmp/audio.mp3",
    output_path="/tmp/output.wav"
)

# Se arquivo já está 16kHz mono, retorna o arquivo original (sem conversão)
if wav_path == "/tmp/audio.mp3":
    print("✓ Conversão skipped: arquivo já está otimizado")
else:
    print(f"✓ Áudio convertido: {wav_path}")

# Limpar arquivo temporário após usar
AudioProcessor.cleanup_temp_file(wav_path)


# ============================================================================
# EXEMPLO 2: Validação prévia de arquivo
# ============================================================================

# Validar arquivo antes de processar
is_valid, metadata = AudioProcessor.validate_audio_file("/tmp/audio.mp3")

if is_valid:
    print("✓ Arquivo válido")
    streams = metadata.get("streams", [])
    print(f"  - Streams: {len(streams)}")
else:
    print("✗ Arquivo corrompido ou inválido")


# ============================================================================
# EXEMPLO 3: Obter informações de áudio
# ============================================================================

info = AudioProcessor.get_audio_info("/tmp/audio.mp3")

if info:
    print(f"Informações do áudio:")
    print(f"  - Duration: {info['duration']:.2f}s")
    print(f"  - Sample rate: {info['sample_rate']} Hz")
    print(f"  - Channels: {info['channels']}")
    print(f"  - Codec: {info['codec']}")
    print(f"  - File size: {info['file_size_mb']:.2f} MB")


# ============================================================================
# EXEMPLO 4: Detectar se precisa conversão
# ============================================================================

# Obter info
audio_info = AudioProcessor.get_audio_info("/tmp/audio.wav")

# Verificar se precisa conversão
if audio_info:
    needs_conversion = AudioProcessor.needs_conversion(audio_info)

    if not needs_conversion:
        print("✓ Arquivo já está otimizado (16kHz mono)")
        print("  - Convertendo deveria ser instantâneo (skip)")
    else:
        print("⚠️  Arquivo precisa conversão")
        print(f"  - Sample rate: {audio_info['sample_rate']} Hz")
        print(f"  - Channels: {audio_info['channels']}")


# ============================================================================
# EXEMPLO 5: Processamento em batch (paralelo)
# ============================================================================


# Lista de arquivos para processar
files_to_convert = [
    "/tmp/audio1.mp3",
    "/tmp/audio2.wav",
    "/tmp/audio3.flac",
    "/tmp/audio4.m4a",
]

# Processar em paralelo
print("Processando em batch (4 threads)...")
start = time.time()

results = BatchAudioProcessor.process_batch(
    file_paths=files_to_convert,
    is_video=False,
    max_workers=4
)

elapsed = time.time() - start

# Analisar resultados
success_count = sum(1 for r in results if r['success'])
print(f"\n✓ Batch concluído em {elapsed:.2f}s")
print(f"  - Processados: {len(results)}")
print(f"  - Sucesso: {success_count}")
print(f"  - Falhas: {len(results) - success_count}")

# Detalhe de cada arquivo
for result in results:
    status = "✓" if result['success'] else "✗"
    duration = result['duration']
    print(f"  {status} {result['file']} ({duration:.2f}s)")
    if result['error']:
        print(f"     Erro: {result['error']}")

# Usar arquivos convertidos
for result in results:
    if result['success']:
        converted_file = result['output']
        # Fazer algo com arquivo convertido...
        print(f"  Transcrever: {converted_file}")

# Limpar todos os temporários após usar
BatchAudioProcessor.cleanup_batch_results(results)


# ============================================================================
# EXEMPLO 6: Calcular speedup de paralelização
# ============================================================================


# Simular tempos (sequential vs paralelo)
sequential_time = 10.0  # segundos
parallel_time = 3.0     # segundos

# Calcular estatísticas
stats = ParallelConversionStats.calculate_speedup(
    sequential_time=sequential_time,
    parallel_time=parallel_time
)

print("Performance Statistics:")
print(f"  - Sequential: {stats['sequential_time_s']:.2f}s")
print(f"  - Parallel:   {stats['parallel_time_s']:.2f}s")
print(f"  - Speedup:    {stats['speedup']:.2f}x")
print(f"  - Efficiency: {stats['efficiency_percent']:.1f}%")
print(f"  - Workers:    {stats['workers']}")


# ============================================================================
# EXEMPLO 7: Processamento de vídeo (batch)
# ============================================================================

# Lista de vídeos para extrair áudio
videos_to_process = [
    "/tmp/video1.mp4",
    "/tmp/video2.mkv",
    "/tmp/video3.mov",
]

# Processar vídeos em paralelo (extração de áudio)
print("Processando vídeos em batch...")
results = BatchAudioProcessor.process_batch(
    file_paths=videos_to_process,
    is_video=True,  # Modo vídeo
    max_workers=2   # Menos threads para vídeos (mais pesados)
)

# Usar áudios extraídos
for result in results:
    if result['success']:
        audio_from_video = result['output']
        print(f"✓ Áudio extraído: {audio_from_video}")
    else:
        print(f"✗ Erro ao extrair áudio: {result['error']}")

# Limpar
BatchAudioProcessor.cleanup_batch_results(results)


# ============================================================================
# EXEMPLO 8: Tratamento de erros
# ============================================================================

try:
    # Tentar converter arquivo inválido
    wav_path = AudioProcessor.convert_to_wav(
        input_path="/tmp/invalid.mp3",
        output_path="/tmp/output.wav"
    )

    if wav_path is None:
        print("✗ Conversão falhou: arquivo inválido ou corrupto")
    else:
        print(f"✓ Arquivo convertido: {wav_path}")

except Exception as e:
    print(f"✗ Erro durante conversão: {e}")


# ============================================================================
# EXEMPLO 9: Integração com Whisper
# ============================================================================


# Converter áudio para formato otimizado
wav_path = AudioProcessor.convert_to_wav(
    input_path="/tmp/audio.mp3",
    output_path="/tmp/temp.wav"
)

if wav_path:
    # Transcrever com Whisper
    transcriber = WhisperTranscriber()
    result = transcriber.transcribe(
        audio_path=wav_path,
        language="pt",
        model_name="medium"
    )

    print(f"Transcrição: {result.text}")
    print(f"Duração: {result.duration:.2f}s")
    print(f"Segmentos: {len(result.segments)}")

    # Limpar
    AudioProcessor.cleanup_temp_file(wav_path)


# ============================================================================
# EXEMPLO 10: Monitoramento de performance
# ============================================================================


# Habilitar logs detalhados
logging.basicConfig(level=logging.INFO)

# Converter com monitoramento
print("\n=== Monitoramento de Performance ===\n")

files = ["/tmp/audio1.mp3", "/tmp/audio2.wav"]

# Teste sequencial
print("📊 Teste SEQUENCIAL:")
start_seq = time.time()
for file in files:
    AudioProcessor.convert_to_wav(file)
time_seq = time.time() - start_seq
print(f"Tempo total: {time_seq:.3f}s\n")

# Teste paralelo
print("📊 Teste PARALELO:")
start_par = time.time()
results = BatchAudioProcessor.process_batch(files, max_workers=2)
time_par = time.time() - start_par
print(f"Tempo total: {time_par:.3f}s\n")

# Comparar
if time_seq > 0:
    speedup = time_seq / time_par
    print(f"📈 Speedup: {speedup:.2f}x")
    print(f"📈 Eficiência: {speedup/len(results)*100:.1f}%")

# Limpar
BatchAudioProcessor.cleanup_batch_results(results)


# ============================================================================
# EXEMPLO 11: Context manager para limpeza automática
# ============================================================================


# Usar context manager para garantir limpeza
with temporary_file("/tmp/temp_audio.wav") as temp_path:
    # Arquivo será automaticamente deletado ao sair do bloco
    wav_path = AudioProcessor.convert_to_wav(
        input_path="/tmp/audio.mp3",
        output_path=temp_path
    )

    if wav_path:
        # Processar aqui...
        print(f"Processando: {wav_path}")
        # Arquivo será limpo automaticamente ao final do bloco

print("✓ Arquivo temporário foi limpado automaticamente")


# ============================================================================
# EXEMPLO 12: Usar com TranscriptionService
# ============================================================================


# Processar arquivo completo (áudio + vídeo)
response = TranscriptionService.process_audio_file(
    file_path="/tmp/video.mp4",
    language="pt",
    model="medium",
    use_cache=True
)

if response.success:
    print(f"✓ Transcrição concluída em {response.processing_time:.2f}s")
    print(f"  - Texto: {response.transcription.text[:100]}...")
    print(f"  - Duração: {response.transcription.duration:.2f}s")
    print(f"  - Segmentos: {len(response.transcription.segments)}")

    if response.audio_info:
        print(f"  - Formato: {response.audio_info.format}")
        print(f"  - Sample rate: {response.audio_info.sample_rate} Hz")
else:
    print(f"✗ Erro: {response.error}")
