#!/usr/bin/env python3
"""
Cliente Python para usar API de transcrição assíncrona com Polling

Este exemplo demonstra como usar o endpoint assíncrono da Daredevil API
com polling ao invés de webhook. Ideal para:
- Desenvolvimento local
- Ambientes com firewall restritivo
- Aplicações que não podem expor webhook público

Uso:
    python transcribe_async_client.py <arquivo_audio> [linguagem]

Exemplo:
    python transcribe_async_client.py audio.mp3 pt
    python transcribe_async_client.py video.mp4 en
"""

import requests
import time
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any


class DaredevilAsyncClient:
    """Cliente para API assíncrona de transcrição com polling"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api", timeout: int = 300):
        """
        Inicializa cliente
        
        Args:
            base_url: URL base da API (padrão: http://localhost:8000/api)
            timeout: Timeout máximo de polling em segundos (padrão: 300 = 5 min)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
    def transcribe(
        self,
        file_path: str,
        language: str = "pt",
        model: Optional[str] = None,
        poll_interval: int = 2,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Transcreve arquivo com polling automático
        
        Args:
            file_path: Caminho do arquivo de áudio/vídeo
            language: Código do idioma (padrão: pt)
            model: Modelo Whisper (tiny, base, small, medium, large)
            poll_interval: Intervalo entre polls em segundos (padrão: 2)
            verbose: Exibir progresso (padrão: True)
            
        Returns:
            Resultado da transcrição com 'success', 'transcription', 'audio_info', etc
        """
        # Step 1: Upload
        if verbose:
            print(f"\n📤 Uploading: {file_path}")
        
        task_id = self._upload_file(file_path, language, model)
        
        if verbose:
            print(f"✅ Upload concluído")
            print(f"📝 Task ID: {task_id}")
            print(f"🔄 Iniciando polling...")
        
        # Step 2: Polling
        result = self._poll_for_result(task_id, poll_interval, verbose)
        
        if verbose:
            print(f"\n✅ Resultado recebido!")
        
        return result
    
    def _upload_file(self, file_path: str, language: str, model: Optional[str]) -> str:
        """Faz upload do arquivo e retorna task_id"""
        # Validar arquivo
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        # Prepare multipart form data
        url = f"{self.base_url}/transcribe/async"
        
        with open(file_path, 'rb') as f:
            files = {'file': (path.name, f)}
            data = {'language': language}
            if model:
                data['model'] = model
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        result = response.json()
        if not result.get('success'):
            raise Exception(f"Upload error: {result.get('error')}")
        
        return result['task_id']
    
    def _poll_for_result(
        self,
        task_id: str,
        poll_interval: int,
        verbose: bool
    ) -> Dict[str, Any]:
        """Faz polling até o resultado estar pronto"""
        start_time = time.time()
        state_prev = None
        
        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                raise TimeoutError(f"Polling timeout após {self.timeout}s")
            
            # Get status
            try:
                status = self._get_status(task_id)
            except Exception as e:
                if verbose:
                    print(f"⚠️  Erro ao consultar status: {e}")
                time.sleep(poll_interval)
                continue
            
            state = status.get('state', 'UNKNOWN')
            
            # Log state change
            if state != state_prev and verbose:
                print(f"  → Estado: {state}")
                state_prev = state
            
            # Handle states
            if state == 'SUCCESS':
                if verbose:
                    print(f"✅ Concluído em {elapsed:.1f}s")
                return status['result']
            
            elif state == 'FAILURE':
                error = status.get('error', 'Unknown error')
                raise Exception(f"Transcrição falhou: {error}")
            
            elif state in ['PENDING', 'STARTED', 'RETRY']:
                if verbose and state_prev != state:
                    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][
                        int(elapsed * 2) % 10
                    ]
                    print(f"  {spinner} {elapsed:.0f}s", end='\r')
                
                time.sleep(poll_interval)
            
            else:
                if verbose:
                    print(f"  ? Estado desconhecido: {state}")
                time.sleep(poll_interval)
    
    def _get_status(self, task_id: str) -> Dict[str, Any]:
        """Consulta o status de uma tarefa"""
        url = f"{self.base_url}/transcribe/async/status/{task_id}"
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.status_code}")
        
        return response.json()
    
    def cancel(self, task_id: str) -> bool:
        """Cancela uma tarefa em progresso"""
        url = f"{self.base_url}/transcribe/async/{task_id}"
        response = requests.delete(url)
        
        if response.status_code != 200:
            raise Exception(f"Cancel failed: {response.status_code}")
        
        result = response.json()
        return result.get('success', False)


def main():
    """Exemplo de uso via linha de comando"""
    
    if len(sys.argv) < 2:
        print("Uso: python transcribe_async_client.py <arquivo> [idioma] [modelo]")
        print("\nExemplos:")
        print("  python transcribe_async_client.py audio.mp3")
        print("  python transcribe_async_client.py audio.mp3 pt medium")
        print("  python transcribe_async_client.py video.mp4 en")
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "pt"
    model = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Create client
    client = DaredevilAsyncClient()
    
    try:
        # Transcribe
        print("\n" + "="*60)
        print("🎤 Daredevil Async Transcription Client")
        print("="*60)
        
        result = client.transcribe(
            file_path=file_path,
            language=language,
            model=model,
            poll_interval=2,
            verbose=True
        )
        
        # Display result
        print("\n" + "="*60)
        print("📝 Resultado:")
        print("="*60)
        
        if result.get('success'):
            transcription = result['transcription']
            
            print(f"\n🎯 Transcrição completa ({result['processing_time']:.1f}s):")
            print("-" * 60)
            print(transcription['text'])
            print("-" * 60)
            
            if transcription.get('segments'):
                print(f"\n📊 Detalhes ({len(transcription['segments'])} segmentos):")
                for i, seg in enumerate(transcription['segments'][:5], 1):
                    print(f"  {i}. [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text'][:60]}")
                if len(transcription['segments']) > 5:
                    print(f"  ... e mais {len(transcription['segments']) - 5} segmentos")
            
            print(f"\n🔊 Informações do áudio:")
            audio_info = result['audio_info']
            print(f"  Format: {audio_info['format']}")
            print(f"  Duration: {audio_info['duration']:.1f}s")
            print(f"  Sample Rate: {audio_info.get('sample_rate', 'N/A')} Hz")
            print(f"  Channels: {audio_info.get('channels', 'N/A')}")
            
            print(f"\n✅ Sucesso!")
        else:
            print(f"❌ Erro: {result.get('error', 'Unknown error')}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
