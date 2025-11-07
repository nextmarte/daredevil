"""
Exemplos de Uso - Conversor Remoto de Áudio

Demonstra como usar a integração com o serviço remoto de conversão.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from transcription.remote_audio_converter import RemoteAudioConverter
from transcription.audio_processor_optimized import AudioProcessor


# ===========================================================================
# EXEMPLO 1: Usar AudioProcessor (recomendado - com fallback automático)
# ===========================================================================

def exemplo_1_audio_processor_basico():
    """
    Forma mais simples de usar - AudioProcessor trata tudo automaticamente.
    
    Comportamento:
    - Tenta conversão remota primeiro
    - Se falhar → retry automático 2x
    - Se ainda falhar → fallback para conversão local
    """
    print("\n" + "="*70)
    print("EXEMPLO 1: Uso Básico com AudioProcessor")
    print("="*70)
    
    # Arquivo de entrada
    input_file = "audio.mp3"
    
    # Converter (remoto com fallback automático)
    print(f"Convertendo: {input_file}")
    result = AudioProcessor.convert_to_wav(input_file)
    
    if result:
        print(f"✅ Conversão bem-sucedida: {result}")
        print(f"   Arquivo pronto para Whisper (transcrição)")
    else:
        print("❌ Conversão falhou")


# ===========================================================================
# EXEMPLO 2: Usar RemoteAudioConverter diretamente
# ===========================================================================

def exemplo_2_remoto_direto():
    """
    Usar cliente remoto diretamente (sem fallback automático).
    
    Use caso: Você quer saber se foi remoto ou local.
    """
    print("\n" + "="*70)
    print("EXEMPLO 2: Cliente Remoto Direto")
    print("="*70)
    
    # Verificar se serviço remoto está disponível
    print("Verificando disponibilidade do serviço remoto...")
    if not RemoteAudioConverter.is_available():
        print("❌ Serviço remoto indisponível")
        print("   Use AudioProcessor para fallback automático")
        return
    
    print("✅ Serviço remoto disponível")
    
    # Obter status
    status = RemoteAudioConverter.get_status()
    if status:
        print(f"\nStatus do conversor remoto:")
        print(f"  Fila: {status.get('queue_length')} tarefas")
        print(f"  Processando: {status.get('active_jobs')} jobs")
        print(f"  Completadas hoje: {status.get('completed_today')}")
        print(f"  Falhas hoje: {status.get('failed_today')}")
        print(f"  Tempo médio: {status.get('avg_conversion_time_seconds')}s")
    
    # Converter com erro handling específico
    input_file = "video.mp4"
    output_file = "audio_converted.wav"
    
    print(f"\nConvertendo: {input_file}")
    result = RemoteAudioConverter.convert_to_wav(input_file, output_file)
    
    if result:
        print(f"✅ Conversão remota bem-sucedida: {result}")
    else:
        print("❌ Conversão remota falhou")


# ===========================================================================
# EXEMPLO 3: Implementar Fallback Manual
# ===========================================================================

def exemplo_3_fallback_manual():
    """
    Controlar manualmente quando usar remoto vs local.
    
    Use caso: Lógica customizada baseada em tamanho de arquivo, etc.
    """
    print("\n" + "="*70)
    print("EXEMPLO 3: Fallback Manual")
    print("="*70)
    
    input_file = "large_video.mp4"
    
    # Obter tamanho do arquivo
    file_size_mb = os.path.getsize(input_file) / (1024 * 1024)
    print(f"Tamanho do arquivo: {file_size_mb:.2f}MB")
    
    # Decisão: usar remoto apenas se arquivo > 50MB
    use_remote = file_size_mb > 50
    
    if use_remote and RemoteAudioConverter.is_available():
        print("📤 Arquivo grande + serviço remoto disponível → usando REMOTO")
        result = RemoteAudioConverter.convert_to_wav(input_file)
    else:
        print("💻 Usando conversão LOCAL")
        result = AudioProcessor._convert_to_wav_local(input_file, "output.wav")
    
    if result:
        print(f"✅ Conversão bem-sucedida: {result}")
    else:
        print("❌ Conversão falhou")


# ===========================================================================
# EXEMPLO 4: Monitorar Status do Serviço Remoto
# ===========================================================================

def exemplo_4_monitorar_status():
    """
    Monitorar saúde e status do serviço remoto em tempo real.
    """
    print("\n" + "="*70)
    print("EXEMPLO 4: Monitorar Serviço Remoto")
    print("="*70)
    
    # Health check
    print("Health Check:")
    health = RemoteAudioConverter.get_health()
    if health:
        print(f"  Status: {health.get('status')}")
        print(f"  FFmpeg: {health.get('ffmpeg_available')}")
        print(f"  Disco: {health.get('disk_usage_percent')}%")
        print(f"  Temp dir: {health.get('temp_dir_size_mb')}MB")
    else:
        print("  ❌ Não foi possível obter health")
    
    # Status detalhado
    print("\nStatus Detalhado:")
    status = RemoteAudioConverter.get_status()
    if status:
        print(f"  Fila: {status.get('queue_length')} tarefas aguardando")
        print(f"  Processando: {status.get('active_jobs')} jobs ativos")
        print(f"  Completadas hoje: {status.get('completed_today')}")
        print(f"  Falhas hoje: {status.get('failed_today')}")
        print(f"  Tempo médio: {status.get('avg_conversion_time_seconds')}s")
        print(f"  Espaço temp: {status.get('temp_dir_size_mb')}MB")
    else:
        print("  ❌ Não foi possível obter status")


# ===========================================================================
# EXEMPLO 5: Tratar Erros Específicos
# ===========================================================================

def exemplo_5_tratamento_erros():
    """
    Tratamento de diferentes tipos de erro.
    """
    print("\n" + "="*70)
    print("EXEMPLO 5: Tratamento de Erros")
    print("="*70)
    
    input_file = "audio.mp3"
    
    # Verificar se arquivo existe
    if not os.path.exists(input_file):
        print(f"❌ Arquivo não encontrado: {input_file}")
        return
    
    try:
        # Tentar conversão
        result = AudioProcessor.convert_to_wav(input_file)
        
        if result is None:
            print("⚠️ Conversão retornou None")
            print("   Possíveis causas:")
            print("   - Arquivo corrompido")
            print("   - Formato não suportado")
            print("   - Erro no ffmpeg")
    
    except FileNotFoundError:
        print("❌ Arquivo de entrada não encontrado")
    
    except IOError:
        print("❌ Erro ao salvar arquivo de saída")
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


# ===========================================================================
# EXEMPLO 6: Usar em Pipeline de Transcrição
# ===========================================================================

def exemplo_6_pipeline_transcricao():
    """
    Usar conversor remoto como parte de pipeline completo.
    """
    print("\n" + "="*70)
    print("EXEMPLO 6: Pipeline Completo de Transcrição")
    print("="*70)
    
    # Arquivo de entrada (áudio ou vídeo)
    input_file = "recording.mp4"
    
    # Passo 1: Converter para WAV 16kHz mono (remoto com fallback)
    print(f"1️⃣  Convertendo áudio: {input_file}")
    converted_audio = AudioProcessor.convert_to_wav(input_file)
    
    if not converted_audio:
        print("❌ Falha na conversão - pipeline abortado")
        return
    
    print(f"✅ Áudio convertido: {converted_audio}")
    
    # Passo 2: Transcrever com Whisper
    print(f"\n2️⃣  Transcrevendo com Whisper...")
    # from transcription.services import TranscriptionService
    # transcription = TranscriptionService.transcribe(converted_audio)
    # print(f"✅ Transcrição: {transcription['text']}")
    
    print("✅ Pipeline completo!")


# ===========================================================================
# EXEMPLO 7: Batch Processing (múltiplos arquivos)
# ===========================================================================

def exemplo_7_batch_processing():
    """
    Processar múltiplos arquivos em lote.
    """
    print("\n" + "="*70)
    print("EXEMPLO 7: Processamento em Lote")
    print("="*70)
    
    # Lista de arquivos para processar
    files = [
        "audio1.mp3",
        "audio2.wav",
        "video1.mp4",
        "audio3.flac"
    ]
    
    results = []
    
    for input_file in files:
        print(f"\nProcessando: {input_file}")
        
        # Converter (com retry e fallback automático)
        result = AudioProcessor.convert_to_wav(input_file)
        
        if result:
            print(f"  ✅ {result}")
            results.append({"input": input_file, "output": result, "status": "ok"})
        else:
            print(f"  ❌ Falha na conversão")
            results.append({"input": input_file, "output": None, "status": "error"})
    
    # Resumo
    print("\n" + "-"*70)
    print("RESUMO:")
    success = len([r for r in results if r["status"] == "ok"])
    failed = len([r for r in results if r["status"] == "error"])
    print(f"✅ Sucesso: {success}/{len(results)}")
    print(f"❌ Falhas: {failed}/{len(results)}")


# ===========================================================================
# EXEMPLO 8: Verificar Performance (Remoto vs Local)
# ===========================================================================

def exemplo_8_benchmark():
    """
    Comparar performance remoto vs local.
    """
    print("\n" + "="*70)
    print("EXEMPLO 8: Benchmark - Remoto vs Local")
    print("="*70)
    
    import time
    
    input_file = "audio.mp3"
    
    # Benchmark REMOTO
    if RemoteAudioConverter.is_available():
        print(f"\nTestando REMOTO:")
        print(f"  Arquivo: {input_file}")
        
        start = time.time()
        result_remote = RemoteAudioConverter.convert_to_wav(
            input_file, 
            "output_remote.wav"
        )
        time_remote = time.time() - start
        
        if result_remote:
            print(f"  Tempo: {time_remote:.2f}s")
            print(f"  ✅ Sucesso")
    else:
        print("\nTestando REMOTO:")
        print("  ❌ Serviço remoto indisponível")
        time_remote = None
    
    # Benchmark LOCAL
    print(f"\nTestando LOCAL:")
    start = time.time()
    result_local = AudioProcessor._convert_to_wav_local(
        input_file,
        "output_local.wav"
    )
    time_local = time.time() - start
    
    if result_local:
        print(f"  Tempo: {time_local:.2f}s")
        print(f"  ✅ Sucesso")
    
    # Comparação
    print("\n" + "-"*70)
    print("COMPARAÇÃO:")
    if time_remote:
        speedup = time_local / time_remote
        print(f"Remoto: {time_remote:.2f}s")
        print(f"Local:  {time_local:.2f}s")
        print(f"Ganho:  {speedup:.1f}x mais rápido 🚀")


# ===========================================================================
# EXECUTAR EXEMPLOS
# ===========================================================================

if __name__ == '__main__':
    print("\n" + "🎯 "*35)
    print("EXEMPLOS DE USO - CONVERSOR REMOTO")
    print("🎯 "*35)
    
    # Descomente os exemplos que quer executar:
    
    # exemplo_1_audio_processor_basico()
    # exemplo_2_remoto_direto()
    # exemplo_3_fallback_manual()
    # exemplo_4_monitorar_status()
    # exemplo_5_tratamento_erros()
    # exemplo_6_pipeline_transcricao()
    # exemplo_7_batch_processing()
    # exemplo_8_benchmark()
    
    print("\n" + "="*70)
    print("Para usar os exemplos, descomente as funções acima!")
    print("="*70)
    print("\nExemplos disponíveis:")
    print("1. exemplo_1_audio_processor_basico()      - Forma mais simples")
    print("2. exemplo_2_remoto_direto()               - Cliente remoto direto")
    print("3. exemplo_3_fallback_manual()             - Controlar fallback")
    print("4. exemplo_4_monitorar_status()            - Monitorar serviço")
    print("5. exemplo_5_tratamento_erros()            - Tratar erros")
    print("6. exemplo_6_pipeline_transcricao()        - Pipeline completo")
    print("7. exemplo_7_batch_processing()            - Processar lotes")
    print("8. exemplo_8_benchmark()                   - Comparar performance")
    print()
