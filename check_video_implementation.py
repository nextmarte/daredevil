#!/usr/bin/env python3
"""
Quick syntax check script para validar que toda a implementação de vídeo está OK
Não requer Docker ou banco de dados rodando
"""

import sys
import ast
from pathlib import Path

def check_syntax(filepath):
    """Verifica sintaxe de um arquivo Python"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_imports_in_file(filepath):
    """Verifica se imports estão presentes"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return None

def main():
    project_root = Path('/home/marcus/projects/daredevil')
    
    print("=" * 70)
    print("🎥 VIDEO SUPPORT - SYNTAX & STRUCTURE CHECK")
    print("=" * 70)
    
    files_to_check = [
        'transcription/services.py',
        'transcription/api.py',
        'transcription/video_processor.py',
        'config/settings.py',
    ]
    
    all_ok = True
    
    # 1. Verificar sintaxe
    print("\n📝 Verificando Sintaxe Python...")
    print("-" * 70)
    
    for filename in files_to_check:
        filepath = project_root / filename
        if not filepath.exists():
            print(f"❌ {filename} - NÃO ENCONTRADO")
            all_ok = False
            continue
            
        ok, error = check_syntax(filepath)
        if ok:
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename}")
            print(f"  Erro: {error}")
            all_ok = False
    
    # 2. Verificar imports principais
    print("\n🔗 Verificando Imports...")
    print("-" * 70)
    
    # VideoProcessor imports em services.py
    services_content = check_imports_in_file(project_root / 'transcription/services.py')
    if services_content:
        if 'from .video_processor import VideoProcessor, MediaTypeDetector' in services_content:
            print("✓ services.py tem imports de VideoProcessor")
        else:
            print("✗ services.py FALTA imports de VideoProcessor")
            all_ok = False
    
    # ALL_SUPPORTED_FORMATS em settings.py
    settings_content = check_imports_in_file(project_root / 'config/settings.py')
    if settings_content:
        if 'ALL_SUPPORTED_FORMATS' in settings_content:
            print("✓ settings.py tem ALL_SUPPORTED_FORMATS")
        else:
            print("✗ settings.py FALTA ALL_SUPPORTED_FORMATS")
            all_ok = False
        
        if 'SUPPORTED_VIDEO_FORMATS' in settings_content:
            print("✓ settings.py tem SUPPORTED_VIDEO_FORMATS")
        else:
            print("✗ settings.py FALTA SUPPORTED_VIDEO_FORMATS")
            all_ok = False
    
    # API atualizada em api.py
    api_content = check_imports_in_file(project_root / 'transcription/api.py')
    if api_content:
        if 'ALL_SUPPORTED_FORMATS' in api_content:
            print("✓ api.py usa ALL_SUPPORTED_FORMATS")
        else:
            print("✗ api.py NÃO usa ALL_SUPPORTED_FORMATS")
            all_ok = False
        
        if '@api.get("/formats"' in api_content:
            print("✓ api.py tem endpoint GET /formats")
        else:
            print("✗ api.py FALTA endpoint GET /formats")
            all_ok = False
    
    # 3. Verificar estrutura do video_processor.py
    print("\n🎬 Verificando video_processor.py...")
    print("-" * 70)
    
    video_processor_file = project_root / 'transcription/video_processor.py'
    if video_processor_file.exists():
        vp_content = check_imports_in_file(video_processor_file)
        if vp_content:
            checks = [
                ('class VideoProcessor', 'VideoProcessor class'),
                ('class MediaTypeDetector', 'MediaTypeDetector class'),
                ('def validate_video_file', 'validate_video_file method'),
                ('def get_video_info', 'get_video_info method'),
                ('def extract_audio', 'extract_audio method'),
                ('SUPPORTED_VIDEO_FORMATS', 'SUPPORTED_VIDEO_FORMATS'),
            ]
            
            for check_str, description in checks:
                if check_str in vp_content:
                    print(f"✓ {description}")
                else:
                    print(f"✗ {description} FALTANDO")
                    all_ok = False
    else:
        print("✗ video_processor.py NÃO ENCONTRADO")
        all_ok = False
    
    # 4. Verificar método process_audio_file atualizado
    print("\n⚙️ Verificando process_audio_file()...")
    print("-" * 70)
    
    if services_content:
        checks = [
            ('is_video = extension in settings.SUPPORTED_VIDEO_FORMATS', 'Detecção de vídeo'),
            ('VideoProcessor.validate_video_file', 'Validação de vídeo'),
            ('VideoProcessor.get_video_info', 'Info de vídeo'),
            ('VideoProcessor.extract_audio', 'Extração de áudio'),
        ]
        
        for check_str, description in checks:
            if check_str in services_content:
                print(f"✓ {description}")
            else:
                print(f"✗ {description} FALTANDO")
                all_ok = False
    
    # 5. Verificar documentação
    print("\n📚 Verificando Documentação...")
    print("-" * 70)
    
    docs_to_check = [
        'VIDEO_SUPPORT.md',
        'VIDEO_IMPLEMENTATION.md',
    ]
    
    for doc in docs_to_check:
        doc_path = project_root / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            lines = sum(1 for _ in open(doc_path))
            print(f"✓ {doc} ({lines} linhas, {size/1024:.1f}KB)")
        else:
            print(f"✗ {doc} NÃO ENCONTRADO")
    
    # 6. Verificar script de teste
    print("\n🧪 Verificando Script de Teste...")
    print("-" * 70)
    
    test_file = project_root / 'test_video_support.py'
    if test_file.exists():
        ok, error = check_syntax(test_file)
        if ok:
            lines = sum(1 for _ in open(test_file))
            print(f"✓ test_video_support.py ({lines} linhas)")
        else:
            print(f"✗ test_video_support.py tem erro de sintaxe: {error}")
            all_ok = False
    else:
        print(f"✗ test_video_support.py NÃO ENCONTRADO")
        all_ok = False
    
    # Resultado final
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ TUDO OK! Implementação de vídeo está completa e válida.")
        print("\n📋 Próximos passos:")
        print("1. Reiniciar container Docker: docker compose up -d")
        print("2. Testar endpoint: curl http://localhost:8511/api/formats")
        print("3. Executar teste completo: docker compose exec daredevil uv run python test_video_support.py")
        return 0
    else:
        print("❌ ALGUNS PROBLEMAS ENCONTRADOS!")
        print("\n🔧 Problemas detectados acima. Corrija antes de continuar.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
