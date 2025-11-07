#!/usr/bin/env python3
"""
Script de teste para validar as correções do erro 502 Proxy
"""
import requests
import json
import time

# URL da API via SSH tunnel (local)
API_URL = "http://localhost:8511"

def test_health():
    """Testa endpoint de health"""
    print("\n=== Testando /api/health ===")
    try:
        response = requests.get(f"{API_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_formats():
    """Testa endpoint de formatos"""
    print("\n=== Testando /api/formats ===")
    try:
        response = requests.get(f"{API_URL}/api/formats")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Áudio: {len(data['audio_formats'])} formatos")
        print(f"Vídeo: {len(data['video_formats'])} formatos")
        print(f"Tamanho máximo: {data['max_size_mb']}MB")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_gpu_status():
    """Testa endpoint de GPU"""
    print("\n=== Testando /api/gpu-status ===")
    try:
        response = requests.get(f"{API_URL}/api/gpu-status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("TESTE DE VALIDAÇÃO DAS CORREÇÕES DO ERRO 502")
    print("=" * 60)
    
    # Aguardar um pouco para certeza de que a API está pronta
    print("\nAguardando API estar pronta...")
    time.sleep(5)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Formatos", test_formats()))
    results.append(("GPU Status", test_gpu_status()))
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("✅ TODOS OS TESTES PASSARAM!" if all_passed else "❌ ALGUNS TESTES FALHARAM"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
