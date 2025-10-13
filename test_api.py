#!/usr/bin/env python3
"""
Script de teste simples para a API Daredevil
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api"


def test_health():
    """Testa endpoint de health check"""
    print("🔍 Testando /api/health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()

        print(f"✅ Status: {data['status']}")
        print(f"   Modelo Whisper: {data['whisper_model']}")
        print(f"   Tamanho máximo: {data['max_file_size_mb']}MB")
        print(
            f"   Formatos suportados: {len(data['supported_formats'])} formatos")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_formats():
    """Testa endpoint de formatos suportados"""
    print("\n🔍 Testando /api/formats...")
    try:
        response = requests.get(f"{BASE_URL}/formats")
        response.raise_for_status()
        data = response.json()

        print(f"✅ Formatos suportados: {', '.join(data['supported_formats'])}")
        print(f"   WhatsApp: {', '.join(data['whatsapp_formats'])}")
        print(f"   Instagram: {', '.join(data['instagram_formats'])}")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_transcribe(audio_file: str):
    """Testa endpoint de transcrição"""
    print(f"\n🔍 Testando /api/transcribe com arquivo: {audio_file}...")
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': f}
            data = {'language': 'pt'}

            response = requests.post(
                f"{BASE_URL}/transcribe", files=files, data=data)
            response.raise_for_status()
            result = response.json()

        if result['success']:
            print(f"✅ Transcrição bem-sucedida!")
            print(f"   Texto: {result['transcription']['text'][:100]}...")
            print(f"   Duração: {result['transcription']['duration']:.2f}s")
            print(f"   Segmentos: {len(result['transcription']['segments'])}")
            print(
                f"   Tempo de processamento: {result['processing_time']:.2f}s")
            print(f"   Formato: {result['audio_info']['format']}")
        else:
            print(f"❌ Falha: {result['error']}")
            return False

        return True
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {audio_file}")
        print("   Para testar transcrição, forneça um arquivo de áudio como argumento:")
        print(f"   python {sys.argv[0]} caminho/do/audio.mp3")
        return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes da API Daredevil\n")
    print("=" * 60)

    # Teste de health
    health_ok = test_health()

    # Teste de formatos
    formats_ok = test_formats()

    # Teste de transcrição (se arquivo fornecido)
    transcribe_ok = None
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        transcribe_ok = test_transcribe(audio_file)
    else:
        print("\n⚠️  Pule o teste de transcrição (nenhum arquivo fornecido)")
        print("   Para testar: python test_api.py caminho/do/audio.mp3")

    # Resumo
    print("\n" + "=" * 60)
    print("📊 Resumo dos Testes:")
    print(f"   Health Check: {'✅ OK' if health_ok else '❌ FALHOU'}")
    print(f"   Formatos: {'✅ OK' if formats_ok else '❌ FALHOU'}")
    if transcribe_ok is not None:
        print(f"   Transcrição: {'✅ OK' if transcribe_ok else '❌ FALHOU'}")

    # Status final
    if health_ok and formats_ok:
        print("\n🎉 API está funcionando corretamente!")
        print("📖 Acesse a documentação em: http://localhost:8000/api/docs")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
