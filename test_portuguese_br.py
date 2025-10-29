#!/usr/bin/env python
"""
Script de teste para verificar suporte a português brasileiro
"""
import requests
import json
import sys

API_BASE = "http://localhost:8511"

def test_transcription_pt_br():
    """Testa transcrição em português brasileiro"""
    print("=" * 70)
    print("🇧🇷 TESTE DE TRANSCRIÇÃO EM PORTUGUÊS BRASILEIRO")
    print("=" * 70)
    
    # URL do arquivo de áudio de teste (você pode substituir por seu próprio)
    # Este é um exemplo usando um arquivo local
    audio_file = "test_audio_pt.mp3"
    
    if not __import__('os').path.exists(audio_file):
        print(f"\n⚠️  Arquivo '{audio_file}' não encontrado")
        print("Para testar, forneça um arquivo de áudio em português")
        return False
    
    print(f"\n📁 Arquivo de teste: {audio_file}")
    print("Enviando para transcrição...\n")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            data = {'language': 'pt'}
            
            response = requests.post(
                f"{API_BASE}/api/transcribe",
                files=files,
                data=data,
                timeout=300
            )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Transcrição concluída!\n")
            print("-" * 70)
            print("📄 RESULTADO:")
            print("-" * 70)
            
            if result.get('success'):
                transcription = result.get('transcription', {})
                
                print(f"\n📝 Texto Completo:")
                print(f"   {transcription.get('text', 'N/A')}\n")
                
                print(f"⏱️  Duração: {transcription.get('duration', 0):.2f}s")
                print(f"⚡ Tempo de processamento: {result.get('processing_time', 0):.2f}s")
                
                # Mostrar segmentos
                segments = transcription.get('segments', [])
                if segments:
                    print(f"\n📊 Segmentos ({len(segments)} total):")
                    for i, seg in enumerate(segments[:5], 1):  # Mostrar primeiros 5
                        print(f"   [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")
                    
                    if len(segments) > 5:
                        print(f"   ... e mais {len(segments) - 5} segmentos")
                
                # Mostrar áudio info
                audio_info = result.get('audio_info', {})
                if audio_info:
                    print(f"\n🔊 Informações do Áudio:")
                    print(f"   Formato: {audio_info.get('format')}")
                    print(f"   Tamanho: {audio_info.get('file_size_mb', 0):.2f}MB")
                    print(f"   Taxa: {audio_info.get('sample_rate', 0)} Hz")
                    print(f"   Canais: {audio_info.get('channels', 0)}")
                
                return True
            else:
                print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        print(f"   Certifique-se de que o servidor está rodando em {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_api_health():
    """Testa se a API está saudável"""
    print("=" * 70)
    print("🏥 VERIFICAÇÃO DE SAÚDE DA API")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API está saudável\n")
            print(f"Status: {data.get('status')}")
            print(f"Modelo Whisper: {data.get('whisper_model')}")
            print(f"Formatos suportados: {', '.join(data.get('supported_formats', []))}")
            return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        return False


def test_gpu_status():
    """Testa status da GPU"""
    print("\n" + "=" * 70)
    print("🎮 VERIFICAÇÃO DE GPU")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_BASE}/api/gpu-status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('gpu_available'):
                print("✅ GPU disponível!\n")
                print(f"Dispositivo: {data.get('device')}")
                print(f"Número de GPUs: {data.get('gpu_count')}")
                
                for gpu in data.get('gpus', []):
                    print(f"\nGPU {gpu['id']}: {gpu['name']}")
                    print(f"  Memória alocada: {gpu['memory_allocated_gb']}GB")
                    print(f"  Memória total: {gpu['memory_total_gb']}GB")
                    print(f"  Memória livre: {gpu['memory_free_gb']}GB")
            else:
                print("⚠️  GPU não disponível (usando CPU)")
                print(f"Mensagem: {data.get('message')}")
            
            return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API")
        return False


def main():
    """Executa testes"""
    print("\n🚀 DAREDEVIL - TESTE DE PORTUGUÊS BRASILEIRO\n")
    
    # Testar saúde da API
    if not test_api_health():
        print("\n❌ API não está respondendo. Inicie com: docker compose up -d")
        return 1
    
    # Testar GPU
    test_gpu_status()
    
    # Testar transcrição (se tiver arquivo)
    print()
    test_transcription_pt_br()
    
    print("\n" + "=" * 70)
    print("✅ Testes concluídos!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
