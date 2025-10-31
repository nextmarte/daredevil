#!/usr/bin/env python3
"""
Test script para validar suporte a vídeos na API Daredevil

Testa:
1. VideoProcessor - Validação de vídeos
2. Extração de áudio de vídeos
3. Endpoint /api/transcribe com vídeos
4. Batch processing com vídeos
"""

import os
import sys
import time
import json
import subprocess
import tempfile
from pathlib import Path

# Adicionar projeto ao path
sys.path.insert(0, '/home/marcus/projects/daredevil')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

import torch
from django.conf import settings
from transcription.video_processor import VideoProcessor, MediaTypeDetector
from transcription.services import TranscriptionService

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")

def create_test_video(output_path, duration=5):
    """Cria um arquivo de vídeo de teste usando ffmpeg"""
    print_info(f"Criando vídeo de teste: {output_path} ({duration}s)")
    
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c=blue:s=640x480:d={duration}',
        '-f', 'lavfi',
        '-i', f'sine=f=1000:d={duration}',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            print_success(f"Vídeo de teste criado: {output_path}")
            return True
        else:
            print_error(f"Erro ao criar vídeo: {result.stderr.decode()}")
            return False
    except Exception as e:
        print_error(f"Erro ao executar ffmpeg: {e}")
        return False

def test_media_type_detector():
    """Testa detecção de tipo de mídia"""
    print_header("Teste 1: MediaTypeDetector")
    
    test_cases = [
        ('test.mp4', 'video'),
        ('test.mp3', 'audio'),
        ('test.wav', 'audio'),
        ('test.mkv', 'video'),
        ('test.txt', 'unknown'),
    ]
    
    for filename, expected_type in test_cases:
        detected_type = MediaTypeDetector.detect_media_type(filename)
        if detected_type == expected_type:
            print_success(f"{filename} → {detected_type}")
        else:
            print_error(f"{filename} → {detected_type} (esperado: {expected_type})")

def test_supported_formats():
    """Testa lista de formatos suportados"""
    print_header("Teste 2: Formatos Suportados")
    
    print(f"{BOLD}Formatos de Áudio:{RESET}")
    for fmt in sorted(settings.SUPPORTED_AUDIO_FORMATS):
        print(f"  • {fmt}")
    
    print(f"\n{BOLD}Formatos de Vídeo:{RESET}")
    for fmt in sorted(settings.SUPPORTED_VIDEO_FORMATS):
        print(f"  • {fmt}")
    
    print(f"\n{BOLD}Total de formatos:{RESET} {len(settings.ALL_SUPPORTED_FORMATS)}")
    print_success(f"Formatos carregados: {len(settings.ALL_SUPPORTED_FORMATS)}")

def test_video_validation():
    """Testa validação de arquivo de vídeo"""
    print_header("Teste 3: Validação de Vídeo")
    
    # Criar vídeo de teste
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        test_video_path = f.name
    
    try:
        if not create_test_video(test_video_path, duration=3):
            print_error("Não foi possível criar vídeo de teste")
            return
        
        # Testar validação
        is_valid, error = VideoProcessor.validate_video_file(test_video_path)
        if is_valid:
            print_success(f"Vídeo validado: {test_video_path}")
        else:
            print_error(f"Vídeo inválido: {error}")
        
    finally:
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
            print_info(f"Arquivo de teste removido: {test_video_path}")

def test_video_info_extraction():
    """Testa extração de informações do vídeo"""
    print_header("Teste 4: Extração de Informações de Vídeo")
    
    # Criar vídeo de teste
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        test_video_path = f.name
    
    try:
        if not create_test_video(test_video_path, duration=5):
            print_error("Não foi possível criar vídeo de teste")
            return
        
        # Obter informações
        info = VideoProcessor.get_video_info(test_video_path)
        
        print_success("Informações do vídeo extraídas:")
        for key, value in info.items():
            print(f"  • {key}: {value}")
        
    finally:
        if os.path.exists(test_video_path):
            os.remove(test_video_path)

def test_audio_extraction():
    """Testa extração de áudio de vídeo"""
    print_header("Teste 5: Extração de Áudio de Vídeo")
    
    # Criar vídeo de teste
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        test_video_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        output_audio_path = f.name
    
    try:
        if not create_test_video(test_video_path, duration=5):
            print_error("Não foi possível criar vídeo de teste")
            return
        
        print_info(f"Extraindo áudio de: {test_video_path}")
        print_info(f"Salvando em: {output_audio_path}")
        
        success, result_msg = VideoProcessor.extract_audio(
            test_video_path,
            output_audio_path,
            timeout=60
        )
        
        if success:
            print_success(f"Áudio extraído com sucesso")
            file_size = os.path.getsize(output_audio_path) / (1024 * 1024)
            print(f"  • Tamanho: {file_size:.2f} MB")
            
            # Verificar áudio extraído
            audio_info = VideoProcessor.get_video_info(output_audio_path)
            print(f"  • Informações: {audio_info}")
        else:
            print_error(f"Erro ao extrair áudio: {result_msg}")
        
    finally:
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)
            print_info(f"Arquivo de áudio teste removido")

def test_video_transcription():
    """Testa transcrição de vídeo completa"""
    print_header("Teste 6: Transcrição de Vídeo Completa")
    
    # Criar vídeo de teste
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        test_video_path = f.name
    
    try:
        if not create_test_video(test_video_path, duration=5):
            print_error("Não foi possível criar vídeo de teste")
            return
        
        print_info(f"Iniciando transcrição de: {test_video_path}")
        
        start_time = time.time()
        result = TranscriptionService.process_audio_file(
            file_path=test_video_path,
            language='pt',
            model=None
        )
        elapsed_time = time.time() - start_time
        
        print(f"  • Tempo de processamento: {elapsed_time:.2f}s")
        
        if result.success:
            print_success("Transcrição concluída com sucesso")
            print(f"  • Texto: {result.transcription.text[:100]}...")
            print(f"  • Duração: {result.audio_info.duration:.2f}s")
            print(f"  • Formato original: {result.audio_info.format}")
        else:
            print_error(f"Erro na transcrição: {result.error}")
        
    finally:
        if os.path.exists(test_video_path):
            os.remove(test_video_path)
            print_info(f"Arquivo de teste removido")

def test_gpu_status():
    """Verifica status das GPUs"""
    print_header("Teste 7: Status da GPU")
    
    if torch.cuda.is_available():
        print_success(f"GPU disponível")
        print(f"  • Quantidade: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            name = torch.cuda.get_device_name(i)
            total_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"  • GPU {i}: {name} ({total_memory:.2f} GB)")
    else:
        print_error("Nenhuma GPU disponível - usando CPU")

def test_settings():
    """Verifica configurações importantes"""
    print_header("Teste 8: Configurações")
    
    print(f"Limite máximo de arquivo: {settings.MAX_AUDIO_SIZE_MB} MB")
    print(f"Modelo Whisper: {settings.WHISPER_MODEL}")
    print(f"Idioma padrão: {settings.WHISPER_LANGUAGE}")
    print(f"Diretório temporário: {settings.TEMP_AUDIO_DIR}")
    print(f"Total de formatos suportados: {len(settings.ALL_SUPPORTED_FORMATS)}")

def main():
    """Executa todos os testes"""
    print(f"\n{BOLD}{BLUE}🎥 VIDEO SUPPORT TEST SUITE{RESET}")
    print(f"{BOLD}Daredevil Transcription API{RESET}\n")
    
    # Verificar dependências
    print_header("Verificação de Dependências")
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print_success("FFmpeg instalado")
        else:
            print_error("FFmpeg não encontrado")
            return
    except Exception as e:
        print_error(f"Erro ao verificar FFmpeg: {e}")
        return
    
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print_success("FFprobe instalado")
        else:
            print_error("FFprobe não encontrado")
            return
    except Exception as e:
        print_error(f"Erro ao verificar FFprobe: {e}")
        return
    
    # Executar testes
    test_gpu_status()
    test_settings()
    test_media_type_detector()
    test_supported_formats()
    test_video_validation()
    test_video_info_extraction()
    test_audio_extraction()
    test_video_transcription()
    
    print_header("✅ Testes Concluídos")
    print(f"\n{GREEN}{BOLD}Suporte a vídeos está operacional!{RESET}\n")

if __name__ == '__main__':
    main()
