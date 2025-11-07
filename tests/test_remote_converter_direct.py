#!/usr/bin/env python
"""
🧪 Teste direto do Remote Audio Converter
Testa conversão de OGG para WAV usando ultron.local:8591
"""

import os
import sys

# Adicionar projeto ao path
sys.path.insert(0, '/home/marcus/projects/daredevil')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from transcription.remote_audio_converter import RemoteAudioConverter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_remote_converter():
    """Testa conversão remota de OGG para WAV"""
    
    input_file = "/home/marcus/projects/daredevil/WhatsApp Audio 2025-10-25 at 14.52.18.ogg"
    output_file = "/tmp/converted_from_ogg.wav"
    
    print("\n" + "="*80)
    print("🔧 TESTE - Remote Audio Converter")
    print("="*80)
    
    print(f"\n📂 Arquivo de entrada: {input_file}")
    print(f"   Tamanho: {os.path.getsize(input_file) / 1024:.1f} KB")
    
    print(f"\n🎯 URL do serviço remoto: {RemoteAudioConverter.REMOTE_CONVERTER_URL}")
    
    # Test 1: Verificar disponibilidade
    print("\n1️⃣  Verificar disponibilidade do serviço remoto...")
    if RemoteAudioConverter.is_available():
        print("   ✅ Serviço DISPONÍVEL")
    else:
        print("   ❌ Serviço NÃO DISPONÍVEL")
        return
    
    # Test 2: Converter arquivo
    print("\n2️⃣  Iniciando conversão remota (OGG → WAV 16kHz mono)...")
    result = RemoteAudioConverter.convert_to_wav(
        input_path=input_file,
        output_path=output_file,
        sample_rate=16000,
        channels=1
    )
    
    if result:
        print(f"   ✅ SUCESSO! Arquivo convertido: {result}")
        size_kb = os.path.getsize(result) / 1024
        print(f"   📊 Tamanho do arquivo convertido: {size_kb:.1f} KB")
    else:
        print(f"   ❌ FALHA na conversão")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_remote_converter()
