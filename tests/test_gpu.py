#!/usr/bin/env python
"""
Script para testar a configuração de GPU no ambiente Daredevil
"""
import sys

def test_torch_gpu():
    """Testa se PyTorch detecta GPU"""
    print("=" * 60)
    print("TESTE DE GPU - PyTorch")
    print("=" * 60)
    
    try:
        import torch
        print(f"✓ PyTorch instalado: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA disponível: {torch.version.cuda}")
            print(f"✓ Número de GPUs: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                print(f"\nGPU {i}:")
                print(f"  - Nome: {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"  - Memória Total: {props.total_memory / (1024**3):.2f} GB")
                print(f"  - Compute Capability: {props.major}.{props.minor}")
                print(f"  - Multiprocessors: {props.multi_processor_count}")
        else:
            print("✗ CUDA não disponível")
            print("Possíveis causas:")
            print("  - GPU NVIDIA não detectada")
            print("  - Drivers NVIDIA não instalados")
            print("  - PyTorch instalado sem suporte CUDA")
            return False
            
        return True
        
    except ImportError:
        print("✗ PyTorch não instalado")
        print("Instale com: uv add torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        return False


def test_whisper_gpu():
    """Testa se Whisper pode usar GPU"""
    print("\n" + "=" * 60)
    print("TESTE DE GPU - Whisper")
    print("=" * 60)
    
    try:
        import whisper
        import torch
        
        print(f"✓ Whisper instalado")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"✓ Dispositivo selecionado: {device}")
        
        if device == "cuda":
            print("\nCarregando modelo Whisper tiny na GPU (teste rápido)...")
            model = whisper.load_model("tiny", device=device)
            print(f"✓ Modelo carregado com sucesso na GPU")
            
            # Verificar memória alocada
            memory_allocated = torch.cuda.memory_allocated(0) / (1024**3)
            print(f"✓ Memória GPU alocada: {memory_allocated:.2f} GB")
            
            return True
        else:
            print("✗ GPU não disponível para Whisper")
            return False
            
    except ImportError:
        print("✗ Whisper não instalado")
        print("Instale com: uv add openai-whisper")
        return False
    except Exception as e:
        print(f"✗ Erro ao carregar modelo Whisper: {e}")
        return False


def test_nvidia_smi():
    """Testa se nvidia-smi está disponível"""
    print("\n" + "=" * 60)
    print("TESTE DE GPU - nvidia-smi")
    print("=" * 60)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✓ nvidia-smi disponível")
            print("\nSaída do nvidia-smi:")
            print("-" * 60)
            print(result.stdout)
            return True
        else:
            print("✗ nvidia-smi retornou erro")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("✗ nvidia-smi não encontrado")
        print("Certifique-se de que os drivers NVIDIA estão instalados")
        return False
    except Exception as e:
        print(f"✗ Erro ao executar nvidia-smi: {e}")
        return False


def test_docker_gpu():
    """Verifica se está rodando em Docker com GPU"""
    print("\n" + "=" * 60)
    print("TESTE DE AMBIENTE")
    print("=" * 60)
    
    import os
    
    # Verificar se está em container
    if os.path.exists('/.dockerenv'):
        print("✓ Rodando em container Docker")
        
        # Verificar variáveis de ambiente relacionadas a GPU
        cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES')
        if cuda_visible:
            print(f"✓ CUDA_VISIBLE_DEVICES: {cuda_visible}")
        else:
            print("  CUDA_VISIBLE_DEVICES não definida")
            
    else:
        print("✓ Rodando no host (não em container)")
    
    # Verificar diretórios CUDA
    if os.path.exists('/usr/local/cuda'):
        print("✓ Diretório CUDA encontrado: /usr/local/cuda")
    else:
        print("  Diretório CUDA não encontrado")
    
    return True


def main():
    """Executa todos os testes"""
    print("\n🚀 Daredevil GPU Test Suite\n")
    
    results = {
        "nvidia-smi": test_nvidia_smi(),
        "torch": test_torch_gpu(),
        "whisper": test_whisper_gpu(),
        "environment": test_docker_gpu(),
    }
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSOU" if passed else "✗ FALHOU"
        print(f"{test_name:20s}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 Todos os testes passaram! GPU configurada corretamente.")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os detalhes acima.")
        print("\nPara mais informações, consulte GPU_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
