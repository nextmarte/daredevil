"""
Exemplos de uso da API Daredevil
"""
import requests


def exemplo_basico():
    """Exemplo básico de transcrição"""
    print("=" * 60)
    print("Exemplo 1: Transcrição Básica")
    print("=" * 60)

    url = "http://localhost:8000/api/transcribe"

    # Substitua pelo caminho do seu arquivo de áudio
    audio_file = "seu_audio.mp3"

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {'language': 'pt'}

        response = requests.post(url, files=files, data=data)
        result = response.json()

    if result['success']:
        print(f"✅ Texto transcrito: {result['transcription']['text']}")
        print(f"⏱️  Tempo de processamento: {result['processing_time']}s")
    else:
        print(f"❌ Erro: {result['error']}")


def exemplo_whatsapp():
    """Exemplo com áudio do WhatsApp"""
    print("\n" + "=" * 60)
    print("Exemplo 2: Áudio do WhatsApp (.opus)")
    print("=" * 60)

    url = "http://localhost:8000/api/transcribe"

    # Áudio do WhatsApp geralmente está em formato .opus
    audio_file = "whatsapp_audio.opus"

    with open(audio_file, 'rb') as f:
        files = {'file': f}
        data = {
            'language': 'pt',
            'model': 'medium'  # Opcional: especificar modelo
        }

        response = requests.post(url, files=files, data=data)
        result = response.json()

    if result['success']:
        print(f"✅ Texto: {result['transcription']['text']}")
        print(f"📊 Segmentos: {len(result['transcription']['segments'])}")

        # Mostrar primeiros 3 segmentos com timestamps
        for i, seg in enumerate(result['transcription']['segments'][:3], 1):
            print(
                f"   {i}. [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")


def exemplo_batch():
    """Exemplo de processamento em lote"""
    print("\n" + "=" * 60)
    print("Exemplo 3: Processamento em Lote")
    print("=" * 60)

    url = "http://localhost:8000/api/transcribe/batch"

    # Lista de arquivos para processar
    arquivos = ["audio1.mp3", "audio2.opus", "audio3.wav"]

    files = []
    for arquivo in arquivos:
        try:
            files.append(('files', open(arquivo, 'rb')))
        except FileNotFoundError:
            print(f"⚠️  Arquivo não encontrado: {arquivo}")

    if files:
        data = {'language': 'pt'}

        response = requests.post(url, files=files, data=data)
        result = response.json()

        print(f"📦 Total de arquivos: {result['total_files']}")
        print(f"✅ Sucessos: {result['successful']}")
        print(f"❌ Falhas: {result['failed']}")
        print(f"⏱️  Tempo total: {result['total_processing_time']}s")

        # Fechar arquivos
        for _, file_obj in files:
            file_obj.close()


def exemplo_health_check():
    """Exemplo de health check"""
    print("\n" + "=" * 60)
    print("Exemplo 4: Health Check")
    print("=" * 60)

    url = "http://localhost:8000/api/health"

    response = requests.get(url)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Modelo Whisper: {result['whisper_model']}")
    print(f"Formatos suportados: {', '.join(result['supported_formats'])}")
    print(f"Tamanho máximo: {result['max_file_size_mb']}MB")


def exemplo_curl():
    """Mostra exemplos de comandos curl"""
    print("\n" + "=" * 60)
    print("Exemplo 5: Usando curl (linha de comando)")
    print("=" * 60)

    exemplos = [
        {
            "titulo": "Transcrição simples",
            "comando": 'curl -X POST "http://localhost:8000/api/transcribe" \\\n  -F "file=@audio.mp3" \\\n  -F "language=pt"'
        },
        {
            "titulo": "WhatsApp áudio",
            "comando": 'curl -X POST "http://localhost:8000/api/transcribe" \\\n  -F "file=@whatsapp.opus" \\\n  -F "language=pt" \\\n  -F "model=medium"'
        },
        {
            "titulo": "Health check",
            "comando": 'curl "http://localhost:8000/api/health"'
        },
        {
            "titulo": "Listar formatos",
            "comando": 'curl "http://localhost:8000/api/formats"'
        }
    ]

    for exemplo in exemplos:
        print(f"\n{exemplo['titulo']}:")
        print(exemplo['comando'])


if __name__ == "__main__":
    print("🎙️  Exemplos de Uso da API Daredevil\n")

    # Apenas mostra os exemplos de curl que sempre funcionam
    exemplo_curl()

    print("\n" + "=" * 60)
    print("📖 Para mais exemplos, veja a documentação em:")
    print("   http://localhost:8000/api/docs")
    print("=" * 60)
