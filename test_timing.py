#!/usr/bin/env python3
"""
Script de teste para verificar se o timing está funcionando corretamente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from transcription.services import TranscriptionService
from pathlib import Path

def test_timing():
    """Testa se as métricas de timing estão sendo retornadas"""
    
    # Procurar por um arquivo de teste
    test_files = [
        "/tmp/daredevil/test_audio.wav",
        "/tmp/test_audio.wav",
    ]
    
    test_file = None
    for f in test_files:
        if os.path.exists(f):
            test_file = f
            break
    
    if not test_file:
        print("❌ Nenhum arquivo de teste encontrado")
        print("   Arquivos procurados:", test_files)
        return False
    
    print(f"✅ Arquivo de teste encontrado: {test_file}")
    print(f"   Tamanho: {os.path.getsize(test_file) / 1024:.1f} KB")
    
    # Processar arquivo
    print("\n🔄 Processando arquivo...")
    result = TranscriptionService.process_audio_file(test_file)
    
    # Verificar resposta
    print(f"\n📊 Resultado:")
    print(f"   Sucesso: {result.success}")
    print(f"   Tempo total: {result.processing_time:.2f}s")
    
    if result.timing_metrics:
        print(f"\n⏱️ Métricas de timing:")
        print(f"   Conversion time: {result.timing_metrics.conversion_time}s")
        print(f"   Model load time: {result.timing_metrics.model_load_time}s")
        print(f"   Transcription time: {result.timing_metrics.transcription_time}s")
        print(f"   Post-processing time: {result.timing_metrics.post_processing_time}s")
        print(f"   Total time: {result.timing_metrics.total_time}s")
    else:
        print("\n❌ Timing metrics não foram retornadas!")
        return False
    
    if result.error:
        print(f"\n❌ Erro: {result.error}")
        return False
    
    if result.transcription:
        print(f"\n📝 Transcrição (primeiros 200 caracteres):")
        print(f"   {result.transcription.text[:200]}...")
    
    print("\n✅ Teste completado com sucesso!")
    return True

if __name__ == '__main__':
    success = test_timing()
    sys.exit(0 if success else 1)
