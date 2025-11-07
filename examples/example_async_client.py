#!/usr/bin/env python3
"""
Exemplo Completo - Conversão Assíncrona com Daredevil

Este script demonstra o fluxo completo:
1. Enfileirar arquivo para conversão
2. Acompanhar progresso
3. Baixar resultado
4. (Opcional) Transcrever com Whisper
"""

import requests
import time
import json
from pathlib import Path
from typing import Optional


class DaredevilAsyncClient:
    """Cliente para API assíncrona do Daredevil."""
    
    def __init__(self, base_url: str = "http://localhost:8511"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def convert_async(
        self,
        file_path: str,
        sample_rate: int = 16000,
        channels: int = 1
    ) -> Optional[str]:
        """
        Enfileira arquivo para conversão assíncrona.
        
        Args:
            file_path: Caminho do arquivo de áudio
            sample_rate: Sample rate em Hz
            channels: Número de canais
        
        Returns:
            job_id ou None se erro
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'sample_rate': sample_rate,
                    'channels': channels
                }
                
                response = requests.post(
                    f"{self.api_url}/convert-async",
                    files=files,
                    data=data
                )
            
            if response.status_code == 202:
                return response.json()['job_id']
            else:
                print(f"❌ Erro: {response.status_code}")
                print(response.json())
                return None
        
        except Exception as e:
            print(f"❌ Erro ao enfileirar: {e}")
            return None
    
    def get_status(self, job_id: str) -> Optional[dict]:
        """Obtém status de uma conversão."""
        try:
            response = requests.get(f"{self.api_url}/convert-status/{job_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
            return None
    
    def wait_for_completion(
        self,
        job_id: str,
        max_wait_seconds: int = 300,
        poll_interval: float = 0.5
    ) -> bool:
        """
        Aguarda completação de uma conversão.
        
        Args:
            job_id: ID do job
            max_wait_seconds: Timeout máximo
            poll_interval: Intervalo de verificação em segundos
        
        Returns:
            True se completou, False se timeout/erro
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            status = self.get_status(job_id)
            
            if not status:
                print(f"❌ Job não encontrado: {job_id}")
                return False
            
            state = status['status']
            progress = status.get('progress', 0)
            
            if state == 'completed':
                print(f"✅ Conversão concluída! ({progress}%)")
                return True
            
            elif state == 'failed':
                error = status.get('error', 'Erro desconhecido')
                print(f"❌ Conversão falhou: {error}")
                return False
            
            else:
                elapsed = time.time() - start_time
                print(
                    f"⏳ {state.upper()} ({progress}%) "
                    f"- {elapsed:.1f}s decorridos"
                )
            
            time.sleep(poll_interval)
        
        print(f"❌ Timeout aguardando conversão (>{max_wait_seconds}s)")
        return False
    
    def download_result(
        self,
        job_id: str,
        output_path: str
    ) -> bool:
        """
        Baixa arquivo convertido.
        
        Args:
            job_id: ID do job
            output_path: Onde salvar arquivo
        
        Returns:
            True se sucesso
        """
        try:
            response = requests.get(f"{self.api_url}/convert-download/{job_id}")
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size_mb = len(response.content) / (1024 * 1024)
                print(f"✅ Arquivo baixado: {output_path} ({file_size_mb:.2f}MB)")
                return True
            
            elif response.status_code == 202:
                print(f"⏳ Conversão ainda em progresso")
                return False
            
            elif response.status_code == 404:
                print(f"❌ Job não encontrado")
                return False
            
            else:
                print(f"❌ Erro ao baixar: {response.status_code}")
                print(response.json())
                return False
        
        except Exception as e:
            print(f"❌ Erro ao baixar: {e}")
            return False
    
    def list_jobs(self) -> list:
        """Lista todos os jobs do usuário."""
        try:
            response = requests.get(f"{self.api_url}/convert-jobs")
            
            if response.status_code == 200:
                return response.json()['jobs']
            else:
                return []
        
        except Exception as e:
            print(f"❌ Erro ao listar jobs: {e}")
            return []
    
    def get_stats(self) -> Optional[dict]:
        """Obtém estatísticas globais."""
        try:
            response = requests.get(f"{self.api_url}/convert-stats")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            print(f"❌ Erro ao obter stats: {e}")
            return None
    
    def convert_and_wait(
        self,
        file_path: str,
        output_path: str,
        **kwargs
    ) -> bool:
        """
        Converte arquivo e aguarda completação (bloqueante).
        
        Exemplo de uso simples:
            >>> client = DaredevilAsyncClient()
            >>> if client.convert_and_wait("audio.mp3", "output.wav"):
            ...     print("Sucesso!")
        """
        # Enfileirar
        print(f"📤 Enfileirando: {file_path}")
        job_id = self.convert_async(file_path, **kwargs)
        
        if not job_id:
            print(f"❌ Falha ao enfileirar")
            return False
        
        print(f"✅ Job enfileirado: {job_id}\n")
        
        # Aguardar
        print(f"⏳ Aguardando conversão...")
        if not self.wait_for_completion(job_id):
            print(f"❌ Conversão falhou")
            return False
        
        print()
        
        # Baixar
        print(f"📥 Baixando resultado...")
        if not self.download_result(job_id, output_path):
            print(f"❌ Falha ao baixar")
            return False
        
        return True


def example_1_simple_conversion():
    """Exemplo 1: Conversão simples e bloqueante."""
    print("\n" + "="*60)
    print("EXEMPLO 1: Conversão Simples")
    print("="*60 + "\n")
    
    client = DaredevilAsyncClient()
    
    # Usar arquivo de teste (ou substitua pelo seu)
    input_file = "test_audio.mp3"
    output_file = "output.wav"
    
    # Criar arquivo de teste se não existir
    if not Path(input_file).exists():
        print(f"⚠️ Arquivo {input_file} não encontrado")
        print("💡 Use: ffmpeg -f lavfi -i sine=f=440:d=5 test_audio.mp3")
        return
    
    # Converter
    success = client.convert_and_wait(input_file, output_file)
    
    if success:
        print(f"🎉 Conversão bem-sucedida!")
        print(f"📁 Arquivo: {output_file}")
    else:
        print(f"❌ Conversão falhou")


def example_2_parallel_conversions():
    """Exemplo 2: Múltiplas conversões paralelas."""
    print("\n" + "="*60)
    print("EXEMPLO 2: Conversões Paralelas")
    print("="*60 + "\n")
    
    client = DaredevilAsyncClient()
    
    # Simular 3 arquivos
    files = ["audio1.mp3", "audio2.mp3", "audio3.mp3"]
    jobs = {}
    
    # Enfileirar todos
    print("📤 Enfileirando 3 conversões...\n")
    for file in files:
        if not Path(file).exists():
            print(f"⚠️ {file} não encontrado")
            continue
        
        job_id = client.convert_async(file)
        if job_id:
            jobs[job_id] = file
            print(f"  ✅ {file}: job {job_id}")
    
    print(f"\n✅ {len(jobs)} conversões enfileiradas\n")
    
    # Aguardar todas
    print("⏳ Aguardando todas as conversões...\n")
    completed = 0
    
    while jobs:
        for job_id, file in list(jobs.items()):
            status = client.get_status(job_id)
            
            if not status:
                print(f"  ❌ {file}: não encontrado")
                del jobs[job_id]
                continue
            
            if status['status'] == 'completed':
                print(f"  ✅ {file}: concluído")
                del jobs[job_id]
                completed += 1
            
            elif status['status'] == 'failed':
                print(f"  ❌ {file}: falhou - {status['error']}")
                del jobs[job_id]
        
        if jobs:
            time.sleep(1)
    
    print(f"\n🎉 {completed} conversões concluídas!")


def example_3_monitoring():
    """Exemplo 3: Monitorar estatísticas em tempo real."""
    print("\n" + "="*60)
    print("EXEMPLO 3: Monitoramento de Stats")
    print("="*60 + "\n")
    
    client = DaredevilAsyncClient()
    
    # Ver stats
    stats = client.get_stats()
    
    if stats:
        print(f"📊 Estatísticas de Conversão:\n")
        print(f"  Total de jobs: {stats['total_jobs']}")
        print(f"  Enfileirados: {stats['queued']}")
        print(f"  Processando: {stats['processing']}")
        print(f"  Completados: {stats['completed']}")
        print(f"  Falhas: {stats['failed']}")
        print(f"  Tempo médio: {stats['avg_time_seconds']}s")
    
    # Listar jobs recentes
    print(f"\n📋 Últimos 5 Jobs:\n")
    jobs = client.list_jobs()[:5]
    
    for job in jobs:
        status = job['status']
        symbol = {
            'completed': '✅',
            'processing': '⏳',
            'queued': '📤',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"  {symbol} {job['job_id'][:8]}... - {status}")


def example_4_with_transcription():
    """Exemplo 4: Converter e transcrever com Whisper."""
    print("\n" + "="*60)
    print("EXEMPLO 4: Converter + Transcrever")
    print("="*60 + "\n")
    
    client = DaredevilAsyncClient()
    
    input_file = "test_audio.mp3"
    wav_file = "converted.wav"
    
    # Validar
    if not Path(input_file).exists():
        print(f"⚠️ Arquivo {input_file} não encontrado")
        return
    
    # Passo 1: Converter
    print(f"1️⃣  Convertendo {input_file}...\n")
    if not client.convert_and_wait(input_file, wav_file):
        print(f"❌ Conversão falhou")
        return
    
    # Passo 2: Transcrever (exemplo)
    print(f"\n2️⃣  Transcrevendo {wav_file}...\n")
    
    try:
        # Importar Whisper
        import whisper
        
        model = whisper.load_model("base")
        result = model.transcribe(wav_file, language="pt")
        
        print(f"📝 Transcrição:")
        print(f"   {result['text']}\n")
        
        print(f"📊 Detalhes:")
        print(f"   Idioma: {result['language']}")
        print(f"   Confiança: {result.get('confidence', 'N/A')}")
    
    except ImportError:
        print(f"⚠️ Whisper não instalado")
        print(f"   pip install openai-whisper")
    
    except Exception as e:
        print(f"❌ Erro na transcrição: {e}")


if __name__ == "__main__":
    print("\n" + "🚀 EXEMPLOS - Conversão Assíncrona Daredevil")
    print("=" * 60)
    
    # Executar exemplos
    # example_1_simple_conversion()
    # example_2_parallel_conversions()
    # example_3_monitoring()
    # example_4_with_transcription()
    
    # Menu interativo
    print("\nEscolha um exemplo:")
    print("  1 - Conversão simples")
    print("  2 - Conversões paralelas")
    print("  3 - Monitoramento de stats")
    print("  4 - Converter + Transcrever")
    print("  0 - Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == "1":
        example_1_simple_conversion()
    elif choice == "2":
        example_2_parallel_conversions()
    elif choice == "3":
        example_3_monitoring()
    elif choice == "4":
        example_4_with_transcription()
    else:
        print("Saindo...")
    
    print("\n")
