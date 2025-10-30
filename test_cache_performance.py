"""
Test script para validar cache e GPU optimizations
"""
import os
import sys
import time
import tempfile
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from transcription.cache_manager import get_cache_manager
from transcription.services import WhisperTranscriber


def test_cache_functionality():
    """Testa funcionalidade básica do cache"""
    print("=" * 60)
    print("TESTE 1: Cache Functionality")
    print("=" * 60)
    
    cache_manager = get_cache_manager()
    
    # Test 1: Set and Get
    print("\n1. Testando set/get...")
    test_data = {
        "transcription": {"text": "teste", "segments": [], "language": "pt", "duration": 10.0},
        "success": True
    }
    cache_manager.set("test_key_123", test_data)
    
    retrieved = cache_manager.get("test_key_123")
    assert retrieved is not None, "Cache GET falhou"
    assert retrieved["transcription"]["text"] == "teste", "Dados recuperados incorretos"
    print("✓ Cache set/get funcionando")
    
    # Test 2: Cache miss
    print("\n2. Testando cache miss...")
    result = cache_manager.get("non_existent_key")
    assert result is None, "Cache deveria retornar None para chave inexistente"
    print("✓ Cache miss funcionando")
    
    # Test 3: Stats
    print("\n3. Testando estatísticas...")
    stats = cache_manager.get_stats()
    print(f"   - Cache size: {stats['size']}")
    print(f"   - Hits: {stats['hits']}")
    print(f"   - Misses: {stats['misses']}")
    print(f"   - Hit rate: {stats['hit_rate']}%")
    print(f"   - TTL: {stats['ttl_seconds']}s")
    assert stats['hits'] > 0, "Deveria ter pelo menos 1 hit"
    assert stats['misses'] > 0, "Deveria ter pelo menos 1 miss"
    print("✓ Estatísticas funcionando")
    
    # Test 4: Clear cache
    print("\n4. Testando clear cache...")
    cache_manager.clear()
    stats = cache_manager.get_stats()
    assert stats['size'] == 0, "Cache deveria estar vazio"
    assert stats['hits'] == 0, "Hits deveriam ser zerados"
    print("✓ Clear cache funcionando")
    
    print("\n" + "=" * 60)
    print("✓ TODOS OS TESTES DE CACHE PASSARAM")
    print("=" * 60)


def test_gpu_monitoring():
    """Testa monitoramento de GPU"""
    print("\n" + "=" * 60)
    print("TESTE 2: GPU Monitoring")
    print("=" * 60)
    
    # Test device detection
    print("\n1. Detectando dispositivo...")
    device = WhisperTranscriber.get_device()
    print(f"   Dispositivo: {device}")
    
    if device == "cuda":
        print("\n2. Verificando memória GPU...")
        memory_info = WhisperTranscriber.check_gpu_memory()
        if memory_info:
            print(f"   - Memória total: {memory_info['total_gb']}GB")
            print(f"   - Memória alocada: {memory_info['allocated_gb']}GB")
            print(f"   - Memória reservada: {memory_info['reserved_gb']}GB")
            print(f"   - Memória livre: {memory_info['free_gb']}GB")
            print(f"   - Uso: {memory_info['usage_percent']}%")
            print("✓ Monitoramento de GPU funcionando")
        else:
            print("⚠ Não foi possível obter informações de memória GPU")
        
        print("\n3. Testando clear GPU memory...")
        WhisperTranscriber.clear_gpu_memory()
        print("✓ Clear GPU memory executado")
        
        print("\n4. Testando CPU fallback check...")
        should_fallback = WhisperTranscriber.should_use_cpu_fallback()
        print(f"   CPU fallback necessário: {should_fallback}")
        print("✓ CPU fallback check funcionando")
    else:
        print("\n⚠ GPU não disponível - testes de GPU pulados")
    
    print("\n" + "=" * 60)
    print("✓ TESTES DE GPU CONCLUÍDOS")
    print("=" * 60)


def test_cache_key_generation():
    """Testa geração de chaves de cache"""
    print("\n" + "=" * 60)
    print("TESTE 3: Cache Key Generation")
    print("=" * 60)
    
    # Criar arquivo temporário de teste
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test audio content")
        temp_file = f.name
    
    try:
        cache_manager = get_cache_manager()
        
        print("\n1. Gerando chave de cache...")
        key1 = cache_manager.generate_cache_key(temp_file, model="medium", language="pt")
        print(f"   Chave gerada: {key1}")
        assert len(key1) == 32, "Chave MD5 deveria ter 32 caracteres"
        print("✓ Chave de cache gerada")
        
        print("\n2. Testando consistência de chaves...")
        key2 = cache_manager.generate_cache_key(temp_file, model="medium", language="pt")
        assert key1 == key2, "Mesmos parâmetros deveriam gerar mesma chave"
        print("✓ Chaves consistentes")
        
        print("\n3. Testando chaves diferentes para parâmetros diferentes...")
        key3 = cache_manager.generate_cache_key(temp_file, model="large", language="pt")
        assert key1 != key3, "Parâmetros diferentes deveriam gerar chaves diferentes"
        print("✓ Chaves diferentes para parâmetros diferentes")
        
    finally:
        os.unlink(temp_file)
    
    print("\n" + "=" * 60)
    print("✓ TESTES DE GERAÇÃO DE CHAVE PASSARAM")
    print("=" * 60)


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print(" INICIANDO TESTES DE PERFORMANCE E CACHE")
    print("🚀" * 30 + "\n")
    
    try:
        test_cache_functionality()
        test_gpu_monitoring()
        test_cache_key_generation()
        
        print("\n" + "✅" * 30)
        print(" TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("✅" * 30 + "\n")
        return 0
        
    except Exception as e:
        print("\n" + "❌" * 30)
        print(f" ERRO: {e}")
        print("❌" * 30 + "\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
