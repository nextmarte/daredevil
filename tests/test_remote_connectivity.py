#!/usr/bin/env python
"""
🧪 Teste de Conectividade com Serviço Remoto
Valida acesso à API em 192.168.1.29:8591
"""

import os
import sys
import requests
import json
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings

def test_connectivity():
    """Testa conectividade com o serviço remoto"""
    
    remote_url = "http://192.168.1.33:8591"
    
    print("=" * 70)
    print("🔗 TESTE DE CONECTIVIDADE - Serviço Remoto")
    print("=" * 70)
    print(f"\n🎯 URL Alvo: {remote_url}\n")
    
    # Test 1: Health check
    print("1️⃣  Health Check (/health)")
    print("-" * 70)
    try:
        response = requests.get(
            f"{remote_url}/health",
            timeout=(5, 5)  # connect, read
        )
        print(f"✅ Status: {response.status_code}")
        try:
            data = response.json()
            print(f"✅ Resposta: {json.dumps(data, indent=2)}")
        except:
            print(f"   Resposta: {response.text}")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Serviço não respondeu em 5s")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    # Test 2: Status endpoint
    print("\n2️⃣  Status do Serviço (/status)")
    print("-" * 70)
    try:
        response = requests.get(
            f"{remote_url}/status",
            timeout=(5, 5)
        )
        print(f"✅ Status: {response.status_code}")
        try:
            data = response.json()
            print(f"✅ Resposta: {json.dumps(data, indent=2)}")
        except:
            print(f"   Resposta: {response.text}")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT - Serviço não respondeu em 5s")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    # Test 3: Upload de arquivo de teste
    print("\n3️⃣  Teste de Upload (POST /convert)")
    print("-" * 70)
    
    # Criar arquivo WAV de teste (1 segundo de silêncio)
    import subprocess
    test_wav = "/tmp/test_connectivity.wav"
    
    try:
        # Gerar WAV com ffmpeg
        cmd = [
            "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono", 
            "-t", "1", "-q:a", "9", "-acodec", "libmp3lame", 
            "-y", test_wav.replace(".wav", ".mp3")
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        
        # Converter para WAV
        cmd = [
            "ffmpeg", "-i", test_wav.replace(".wav", ".mp3"),
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            "-y", test_wav
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        
        if os.path.exists(test_wav):
            file_size = os.path.getsize(test_wav)
            print(f"✅ Arquivo de teste criado: {test_wav} ({file_size} bytes)")
            
            # Enviar para conversão
            with open(test_wav, 'rb') as f:
                files = {'file': f}
                data = {'sample_rate': 16000, 'channels': 1}
                
                try:
                    response = requests.post(
                        f"{remote_url}/convert",
                        files=files,
                        data=data,
                        timeout=(5, 30)  # connect, upload
                    )
                    print(f"✅ Status: {response.status_code}")
                    try:
                        data = response.json()
                        print(f"✅ Resposta: {json.dumps(data, indent=2)}")
                    except:
                        print(f"   Resposta: {response.text}")
                except requests.exceptions.Timeout:
                    print("❌ TIMEOUT - Serviço não respondeu")
                except requests.exceptions.ConnectionError as e:
                    print(f"❌ ERRO DE CONEXÃO: {e}")
                except Exception as e:
                    print(f"❌ ERRO: {e}")
        else:
            print("⚠️  Não foi possível criar arquivo de teste")
    except Exception as e:
        print(f"❌ Erro ao preparar arquivo de teste: {e}")
    
    # Test 4: Connection pooling info
    print("\n4️⃣  Informações de Rede")
    print("-" * 70)
    print(f"REMOTE_CONVERTER_URL: {os.getenv('REMOTE_CONVERTER_URL', 'NOT SET')}")
    print(f"TEMP_AUDIO_DIR: {settings.TEMP_AUDIO_DIR}")
    
    print("\n" + "=" * 70)
    print("✅ Testes Concluídos!")
    print("=" * 70)

if __name__ == "__main__":
    test_connectivity()
