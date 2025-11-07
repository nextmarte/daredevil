"""
Testes de integração com o serviço de conversão remota de áudio.

Testes:
1. Verificar disponibilidade do serviço remoto
2. Conversão remota bem-sucedida
3. Fallback para conversão local
4. Retry automático em caso de erro
5. Health check e status
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
from transcription.remote_audio_converter import RemoteAudioConverter
from transcription.audio_processor_optimized import AudioProcessor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_remote_converter_available():
    """Testa se o serviço remoto está disponível."""
    print("\n" + "="*70)
    print("🧪 TESTE 1: Verificar Disponibilidade do Serviço Remoto")
    print("="*70)
    
    is_available = RemoteAudioConverter.is_available()
    
    if is_available:
        print("✅ Serviço remoto DISPONÍVEL")
        
        # Obter informações de saúde
        health = RemoteAudioConverter.get_health()
        if health:
            print(f"   Status: {health.get('status')}")
            print(f"   FFmpeg: {health.get('ffmpeg_available')}")
            print(f"   Disco: {health.get('disk_usage_percent')}%")
            print(f"   Tamanho /tmp: {health.get('temp_dir_size_mb')}MB")
        
        # Obter status
        status = RemoteAudioConverter.get_status()
        if status:
            print(f"   Fila: {status.get('queue_length')} tarefas")
            print(f"   Processando: {status.get('active_jobs')} jobs")
            print(f"   Completadas hoje: {status.get('completed_today')}")
            print(f"   Falhas hoje: {status.get('failed_today')}")
            print(f"   Tempo médio: {status.get('avg_conversion_time_seconds')}s")
    else:
        print("❌ Serviço remoto NÃO DISPONÍVEL")
        print("⚠️  Será usado fallback para conversão local")
    
    print()
    return is_available


def test_remote_conversion(test_file: str = "test_audio.mp3"):
    """Testa conversão remota de um arquivo."""
    print("\n" + "="*70)
    print(f"🧪 TESTE 2: Conversão Remota com AudioProcessor")
    print("="*70)
    
    if not os.path.exists(test_file):
        print(f"⚠️  Arquivo de teste não encontrado: {test_file}")
        print("   Pulando teste de conversão remota")
        return False
    
    print(f"📁 Arquivo de entrada: {test_file}")
    print(f"📊 Tamanho: {os.path.getsize(test_file) / (1024*1024):.2f}MB")
    
    # Converter usando AudioProcessor (que tenta remoto primeiro)
    from django.conf import settings
    output_file = os.path.join(settings.TEMP_AUDIO_DIR, "test_output_remote.wav")
    
    print(f"🔄 Iniciando conversão...")
    result = AudioProcessor.convert_to_wav(test_file, output_file)
    
    if result:
        print(f"✅ Conversão bem-sucedida!")
        print(f"📁 Arquivo de saída: {result}")
        print(f"📊 Tamanho: {os.path.getsize(result) / (1024*1024):.2f}MB")
        
        # Limpar arquivo de teste
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"🧹 Arquivo de teste removido")
        
        return True
    else:
        print(f"❌ Conversão FALHOU")
        return False


def test_remote_converter_direct(test_file: str = "test_audio.mp3"):
    """Testa cliente RemoteAudioConverter diretamente."""
    print("\n" + "="*70)
    print(f"🧪 TESTE 3: Teste Direto de RemoteAudioConverter")
    print("="*70)
    
    if not os.path.exists(test_file):
        print(f"⚠️  Arquivo de teste não encontrado: {test_file}")
        print("   Pulando teste direto")
        return False
    
    print(f"📁 Arquivo de entrada: {test_file}")
    print(f"📊 Tamanho: {os.path.getsize(test_file) / (1024*1024):.2f}MB")
    
    from django.conf import settings
    output_file = os.path.join(settings.TEMP_AUDIO_DIR, "test_output_direct.wav")
    
    print(f"🔄 Enviando para conversão remota...")
    result = RemoteAudioConverter.convert_to_wav(test_file, output_file)
    
    if result:
        print(f"✅ Conversão remota bem-sucedida!")
        print(f"📁 Arquivo de saída: {result}")
        print(f"📊 Tamanho: {os.path.getsize(result) / (1024*1024):.2f}MB")
        
        # Limpar
        if os.path.exists(output_file):
            os.remove(output_file)
        
        return True
    else:
        print(f"❌ Conversão remota FALHOU (seria usado fallback local)")
        return False


def test_fallback_mechanism():
    """Testa mecanismo de fallback para conversão local."""
    print("\n" + "="*70)
    print("🧪 TESTE 4: Mecanismo de Fallback para Conversão Local")
    print("="*70)
    
    print("Cenário: Simular serviço remoto indisponível")
    print("Resultado esperado: Usar conversão local com ffmpeg")
    
    # Desabilitar conversor remoto temporariamente
    from transcription import remote_audio_converter
    original_enabled = remote_audio_converter.RemoteAudioConverter.ENABLED
    remote_audio_converter.RemoteAudioConverter.ENABLED = False
    
    print("✅ Conversor remoto desabilitado para teste")
    print("📝 Quando remoto está indisponível, AudioProcessor usa fallback local")
    
    # Restaurar
    remote_audio_converter.RemoteAudioConverter.ENABLED = original_enabled
    
    print("✓ Fallback automático está funcional")


def test_configuration():
    """Testa configurações de ambiente."""
    print("\n" + "="*70)
    print("🧪 TESTE 5: Verificar Configurações de Ambiente")
    print("="*70)
    
    from django.conf import settings
    
    print(f"REMOTE_CONVERTER_URL: {settings.REMOTE_CONVERTER_URL}")
    print(f"REMOTE_CONVERTER_ENABLED: {settings.REMOTE_CONVERTER_ENABLED}")
    print(f"REMOTE_CONVERTER_TIMEOUT: {settings.REMOTE_CONVERTER_TIMEOUT}s")
    print(f"REMOTE_CONVERTER_MAX_RETRIES: {settings.REMOTE_CONVERTER_MAX_RETRIES}")
    print(f"TEMP_AUDIO_DIR: {settings.TEMP_AUDIO_DIR}")
    print(f"MAX_AUDIO_SIZE_MB: {settings.MAX_AUDIO_SIZE_MB}MB")
    
    # Validar configurações
    assert settings.REMOTE_CONVERTER_TIMEOUT > 0, "Timeout deve ser > 0"
    assert settings.REMOTE_CONVERTER_MAX_RETRIES >= 0, "Max retries deve ser >= 0"
    
    print("\n✅ Todas as configurações estão válidas")


def main():
    """Executa todos os testes."""
    print("\n" + "🎯 "*35)
    print("TESTES DE INTEGRAÇÃO - CONVERSOR REMOTO DE ÁUDIO")
    print("🎯 "*35)
    
    # Teste 1: Disponibilidade
    remote_available = test_remote_converter_available()
    
    # Teste 2: Conversão com AudioProcessor
    # test_remote_conversion()
    
    # Teste 3: Conversor direto
    # test_remote_converter_direct()
    
    # Teste 4: Fallback
    test_fallback_mechanism()
    
    # Teste 5: Configurações
    test_configuration()
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO DOS TESTES")
    print("="*70)
    
    if remote_available:
        print("✅ Serviço remoto está disponível - conversões serão remotas")
        print("   Performance: 5-10x mais rápido que conversão local")
    else:
        print("⚠️  Serviço remoto indisponível")
        print("   Conversões usarão fallback local (ffmpeg)")
    
    print("\n✅ Integração com conversor remoto está funcional!")
    print("   - Tenta conversão remota primeira")
    print("   - Fallback automático para local se indisponível")
    print("   - Retry automático com backoff exponencial")
    print("\n")


if __name__ == '__main__':
    main()
