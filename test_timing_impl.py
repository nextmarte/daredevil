#!/usr/bin/env python3
"""
Teste da implementação de timing metrics
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/marcus/projects/daredevil')
django.setup()

from transcription.services import TranscriptionService

def test_timing_with_local_file():
    """Testa se as métricas de timing estão sendo retornadas com arquivo local"""
    
    # Usar arquivo de teste que existe
    test_file = "/home/marcus/projects/daredevil/tests/test_audio.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Arquivo de teste não encontrado: {test_file}")
        return False
    
    print(f"✅ Arquivo de teste encontrado: {test_file}")
    file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
    print(f"   Tamanho: {file_size_mb:.2f} MB")
    
    # Processar arquivo
    print("\n🔄 Processando arquivo com TranscriptionService...")
    try:
        result = TranscriptionService.process_audio_file(test_file, language='pt')
        
        # Verificar resposta
        print(f"\n📊 Resultado:")
        print(f"   Sucesso: {result.success}")
        print(f"   Tempo total (processing_time): {result.processing_time:.2f}s")
        
        if result.error:
            print(f"   ❌ Erro: {result.error}")
            return False
        
        # Verificar timing_metrics
        if result.timing_metrics is None:
            print(f"\n⚠️  AVISO: Timing metrics é None!")
            print("   Isso pode ocorrer se o cache foi usado ou houve um erro")
        else:
            print(f"\n⏱️ Métricas de timing (timing_metrics):")
            metrics = result.timing_metrics
            if metrics.conversion_time is not None:
                print(f"   📤 Tempo de conversão: {metrics.conversion_time:.2f}s")
            else:
                print(f"   📤 Tempo de conversão: N/A (nenhuma conversão necessária)")
            
            if metrics.model_load_time is not None:
                print(f"   🤖 Tempo de carregamento do modelo: {metrics.model_load_time:.2f}s")
            else:
                print(f"   🤖 Tempo de carregamento do modelo: (incluído na transcrição)")
            
            print(f"   🎙️  Tempo de transcrição: {metrics.transcription_time:.2f}s")
            
            if metrics.post_processing_time is not None:
                print(f"   ✨ Tempo de pós-processamento: {metrics.post_processing_time:.2f}s")
            else:
                print(f"   ✨ Tempo de pós-processamento: (incluído na transcrição)")
            
            print(f"   ⏲️  Tempo total: {metrics.total_time:.2f}s")
        
        # Mostrar resultado da transcrição
        if result.transcription:
            print(f"\n📝 Transcrição (primeiros 300 caracteres):")
            text_preview = result.transcription.text[:300]
            print(f"   {text_preview}...")
            print(f"\n   Idioma: {result.transcription.language}")
            print(f"   Duração do áudio: {result.transcription.duration:.2f}s")
            print(f"   Segmentos: {len(result.transcription.segments)}")
        
        # Mostrar audio_info
        if result.audio_info:
            print(f"\n🎵 Informações do áudio:")
            print(f"   Formato: {result.audio_info.format}")
            print(f"   Duração: {result.audio_info.duration:.2f}s")
            print(f"   Sample rate: {result.audio_info.sample_rate} Hz")
            print(f"   Canais: {result.audio_info.channels}")
            print(f"   Tamanho do arquivo: {result.audio_info.file_size_mb:.2f} MB")
        
        print("\n✅ Teste completado com sucesso!")
        print("\n📋 RESUMO DAS MÉTRICAS:")
        print("=" * 60)
        if result.timing_metrics:
            print(f"Conversão:     {result.timing_metrics.conversion_time or 'N/A':>10} segundos")
            print(f"Transcrição:   {result.timing_metrics.transcription_time:>10.2f} segundos")
            print(f"TOTAL:         {result.timing_metrics.total_time:>10.2f} segundos")
        else:
            print(f"TOTAL:         {result.processing_time:>10.2f} segundos")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante processamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_timing_with_local_file()
    sys.exit(0 if success else 1)
