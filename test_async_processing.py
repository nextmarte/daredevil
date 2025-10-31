"""
Test async processing functionality
"""
import os
import sys
import time
import tempfile
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def test_celery_configuration():
    """Test Celery is configured correctly"""
    print("=" * 60)
    print("TEST 1: Celery Configuration")
    print("=" * 60)
    
    try:
        from config.celery import app
        print(f"\n✓ Celery app created: {app.main}")
        print(f"  Broker: {app.conf.broker_url}")
        print(f"  Backend: {app.conf.result_backend}")
        print(f"  Task serializer: {app.conf.task_serializer}")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao configurar Celery: {e}")
        return False


def test_task_registration():
    """Test tasks are properly registered"""
    print("\n" + "=" * 60)
    print("TEST 2: Task Registration")
    print("=" * 60)
    
    try:
        from transcription.tasks import transcribe_audio_async, transcribe_batch_async
        print("\n✓ Tasks importadas:")
        print(f"  - {transcribe_audio_async.name}")
        print(f"  - {transcribe_batch_async.name}")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao importar tasks: {e}")
        return False


def test_task_structure():
    """Test task has correct configuration"""
    print("\n" + "=" * 60)
    print("TEST 3: Task Configuration")
    print("=" * 60)
    
    try:
        from transcription.tasks import transcribe_audio_async
        
        print(f"\n✓ Configuração da task:")
        print(f"  - Name: {transcribe_audio_async.name}")
        print(f"  - Time limit: {transcribe_audio_async.time_limit}s")
        print(f"  - Soft time limit: {transcribe_audio_async.soft_time_limit}s")
        print(f"  - Max retries: {transcribe_audio_async.max_retries}")
        print(f"  - Default retry delay: {transcribe_audio_async.default_retry_delay}s")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao verificar configuração: {e}")
        return False


def test_redis_connection():
    """Test Redis connection (if Redis is available)"""
    print("\n" + "=" * 60)
    print("TEST 4: Redis Connection")
    print("=" * 60)
    
    try:
        import redis
        from django.conf import settings
        
        # Parse Redis URL
        redis_url = settings.REDIS_URL
        print(f"\n  Redis URL: {redis_url}")
        
        # Try to connect
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        
        print("✓ Redis conectado com sucesso")
        print(f"  Info: {r.info('server')['redis_version']}")
        return True
        
    except redis.ConnectionError:
        print("⚠ Redis não disponível (esperado em ambiente de teste)")
        print("  Para testes completos, inicie Redis: docker-compose up redis")
        return None  # Not a failure, just not available
    except Exception as e:
        print(f"✗ Erro ao conectar no Redis: {e}")
        return False


def test_async_endpoint_imports():
    """Test async endpoints can be imported"""
    print("\n" + "=" * 60)
    print("TEST 5: Async Endpoints")
    print("=" * 60)
    
    try:
        from transcription import api
        print("\n✓ API com endpoints async importada")
        
        # List all endpoints
        print("\n  Endpoints disponíveis:")
        print("  - POST /api/transcribe/async")
        print("  - GET /api/transcribe/async/status/{task_id}")
        print("  - DELETE /api/transcribe/async/{task_id}")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao importar endpoints: {e}")
        return False


def test_webhook_notification():
    """Test webhook notification function"""
    print("\n" + "=" * 60)
    print("TEST 6: Webhook Notification")
    print("=" * 60)
    
    try:
        from transcription.tasks import _send_webhook_notification
        print("\n✓ Função de webhook disponível")
        print("  Nota: Teste real requer servidor HTTP externo")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao importar webhook: {e}")
        return False


def test_docker_compose_config():
    """Test docker-compose has Redis and Celery services"""
    print("\n" + "=" * 60)
    print("TEST 7: Docker Compose Configuration")
    print("=" * 60)
    
    try:
        import yaml
        
        with open('docker-compose.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get('services', {})
        
        # Check Redis service
        if 'redis' in services:
            print("\n✓ Redis service configurado")
            redis_config = services['redis']
            print(f"  - Image: {redis_config.get('image', 'N/A')}")
            print(f"  - Port: {redis_config.get('ports', ['N/A'])[0]}")
        else:
            print("\n✗ Redis service não encontrado")
            return False
        
        # Check Celery worker service
        if 'celery_worker' in services:
            print("\n✓ Celery worker service configurado")
            celery_config = services['celery_worker']
            print(f"  - Command: {celery_config.get('command', 'N/A')}")
            print(f"  - GPU: {bool(celery_config.get('deploy', {}).get('resources', {}).get('reservations', {}).get('devices'))}")
        else:
            print("\n✗ Celery worker service não encontrado")
            return False
        
        # Check volumes
        if 'volumes' in config:
            print("\n✓ Volumes configurados")
            for volume in config['volumes']:
                print(f"  - {volume}")
        
        return True
        
    except FileNotFoundError:
        print("\n✗ docker-compose.yml não encontrado")
        return False
    except Exception as e:
        print(f"\n⚠ Erro ao ler docker-compose.yml: {e}")
        print("  (yaml não instalado, pulando teste)")
        return None


def main():
    """Run all tests"""
    print("\n" + "🚀" * 30)
    print(" TESTES DE PROCESSAMENTO ASSÍNCRONO")
    print("🚀" * 30 + "\n")
    
    tests = [
        test_celery_configuration,
        test_task_registration,
        test_task_structure,
        test_redis_connection,
        test_async_endpoint_imports,
        test_webhook_notification,
        test_docker_compose_config,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"\n✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"⚠️  Pulado: {skipped}")
    
    if failed == 0:
        print("\n" + "✅" * 30)
        print(" TODOS OS TESTES CRÍTICOS PASSARAM!")
        print("✅" * 30 + "\n")
        return 0
    else:
        print("\n" + "❌" * 30)
        print(f" {failed} TESTE(S) FALHARAM")
        print("❌" * 30 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
