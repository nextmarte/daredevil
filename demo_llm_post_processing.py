#!/usr/bin/env python
"""
Script de demonstração do pós-processamento com LLM (Qwen3:30b)
Demonstra correção gramatical avançada e identificação de interlocutores usando IA
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcription.post_processing import LLMPostProcessingService


def example_basic_llm_processing():
    """Exemplo básico de processamento com LLM"""
    print("=" * 80)
    print("EXEMPLO 1: Processamento Básico com LLM (Qwen3:30b)")
    print("=" * 80)
    
    # Simular segmentos de uma conversa com erros
    segments = [
        {'start': 0.0, 'end': 2.5, 'text': 'ola tudo bem com voce', 'confidence': 0.95},
        {'start': 3.0, 'end': 5.0, 'text': 'sim to bem e voce', 'confidence': 0.92},
        {'start': 6.0, 'end': 8.5, 'text': 'tambem to bem obrigado', 'confidence': 0.94},
        {'start': 9.0, 'end': 11.0, 'text': 'qual e o assunto de hoje', 'confidence': 0.93},
        {'start': 11.5, 'end': 14.0, 'text': 'vamos discutir o projeto novo', 'confidence': 0.96}
    ]
    
    raw_text = ' '.join([seg['text'] for seg in segments])
    
    print("\nTexto Original (com erros):")
    print(raw_text)
    
    # Inicializar serviço LLM
    try:
        llm_service = LLMPostProcessingService(
            model_name="qwen3:30b",
            ollama_url="http://localhost:11434/api/generate"
        )
        
        print("\nProcessando com LLM...")
        corrected_text, processed_segments = llm_service.process_transcription(
            segments=segments,
            raw_text=raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        print("\nTexto Corrigido pelo LLM:")
        print(corrected_text)
        
        print("\nSegmentos Processados:")
        for seg in processed_segments:
            speaker_info = f"{seg.speaker_id}: " if seg.speaker_id else ""
            print(f"  [{seg.start:.1f}s - {seg.end:.1f}s] {speaker_info}{seg.corrected_text}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nVerifique se o Ollama está rodando e o modelo qwen3:30b está instalado:")
        print("  1. Instale o Ollama: https://ollama.ai/")
        print("  2. Execute: ollama pull qwen3:30b")
        print("  3. Inicie o servidor: ollama serve")


def example_conversation_with_hesitations():
    """Exemplo de conversa com hesitações"""
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Conversa com Hesitações e Erros")
    print("=" * 80)
    
    segments = [
        {'start': 0.0, 'end': 3.0, 'text': 'e entao né voce ja viu o relatorio', 'confidence': 0.88},
        {'start': 3.5, 'end': 6.0, 'text': 'ah sim vi sim mas tinha uns erro la', 'confidence': 0.90},
        {'start': 6.5, 'end': 9.0, 'text': 'er que tipo de erro voce encontro', 'confidence': 0.87},
        {'start': 9.5, 'end': 12.0, 'text': 'hmm tinha uns numero que nao bate', 'confidence': 0.85}
    ]
    
    raw_text = ' '.join([seg['text'] for seg in segments])
    
    print("\nTexto Original:")
    print(raw_text)
    
    try:
        llm_service = LLMPostProcessingService(model_name="qwen3:30b")
        
        print("\nProcessando com LLM (removendo hesitações e corrigindo)...")
        corrected_text, processed_segments = llm_service.process_transcription(
            segments=segments,
            raw_text=raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        print("\nTexto Corrigido:")
        print(corrected_text)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o Ollama está rodando com o modelo qwen3:30b")


def example_speaker_identification():
    """Exemplo focado em identificação de interlocutores"""
    print("\n" + "=" * 80)
    print("EXEMPLO 3: Identificação Avançada de Interlocutores com LLM")
    print("=" * 80)
    
    segments = [
        {'start': 0.0, 'end': 2.0, 'text': 'bom dia pessoal', 'confidence': 0.95},
        {'start': 2.5, 'end': 4.0, 'text': 'oi bom dia como vai', 'confidence': 0.93},
        {'start': 4.5, 'end': 6.0, 'text': 'tudo otimo e voce', 'confidence': 0.94},
        {'start': 6.5, 'end': 8.0, 'text': 'tambem vamos comecar', 'confidence': 0.92},
        {'start': 8.5, 'end': 10.0, 'text': 'pode comecar sim', 'confidence': 0.95},
        {'start': 10.5, 'end': 13.0, 'text': 'entao o primeiro ponto da pauta e o orcamento', 'confidence': 0.91}
    ]
    
    raw_text = ' '.join([seg['text'] for seg in segments])
    
    print("\nTexto Original:")
    print(raw_text)
    
    try:
        llm_service = LLMPostProcessingService(model_name="qwen3:30b")
        
        print("\nProcessando com LLM para identificar interlocutores...")
        corrected_text, processed_segments = llm_service.process_transcription(
            segments=segments,
            raw_text=raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        print("\nTexto com Interlocutores Identificados:")
        print(corrected_text)
        
        # Contar interlocutores únicos
        speakers = set(seg.speaker_id for seg in processed_segments if seg.speaker_id)
        if speakers:
            print(f"\nTotal de interlocutores detectados: {len(speakers)}")
            print(f"Interlocutores: {', '.join(sorted(speakers))}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("Certifique-se de que o Ollama está rodando com o modelo qwen3:30b")


def check_ollama_connection():
    """Verifica se o Ollama está acessível"""
    print("=" * 80)
    print("VERIFICAÇÃO DO OLLAMA")
    print("=" * 80)
    
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama está rodando!")
            print(f"\nModelos disponíveis: {len(models)}")
            
            qwen_models = [m['name'] for m in models if 'qwen' in m['name'].lower()]
            if qwen_models:
                print(f"Modelos Qwen encontrados: {', '.join(qwen_models)}")
                
                if any('qwen3:30b' in m for m in qwen_models):
                    print("✅ Modelo qwen3:30b está instalado!")
                else:
                    print("⚠️  Modelo qwen3:30b não encontrado. Instale com: ollama pull qwen3:30b")
            else:
                print("⚠️  Nenhum modelo Qwen encontrado. Instale com: ollama pull qwen3:30b")
        else:
            print("❌ Ollama não está respondendo corretamente")
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao Ollama")
        print("\nPara instalar e usar o Ollama:")
        print("  1. Baixe em: https://ollama.ai/")
        print("  2. Instale o aplicativo")
        print("  3. Execute: ollama pull qwen3:30b")
        print("  4. Inicie o servidor: ollama serve")
    except Exception as e:
        print(f"❌ Erro ao verificar Ollama: {e}")


if __name__ == '__main__':
    print("\n" + "🤖 " * 20)
    print("DEMONSTRAÇÃO DO SISTEMA DE PÓS-PROCESSAMENTO COM LLM")
    print("Modelo: Qwen3:30b via Ollama")
    print("🤖 " * 20 + "\n")
    
    # Verificar conexão com Ollama
    check_ollama_connection()
    
    print("\n")
    input("Pressione ENTER para continuar com os exemplos...")
    
    # Executar exemplos
    example_basic_llm_processing()
    example_conversation_with_hesitations()
    example_speaker_identification()
    
    print("\n" + "=" * 80)
    print("✅ Demonstração concluída!")
    print("=" * 80)
    print("\nDicas:")
    print("  - O modelo qwen3:30b oferece correções mais precisas que o processamento tradicional")
    print("  - Ideal para conversas complexas com múltiplos interlocutores")
    print("  - Pode ser habilitado via API usando o parâmetro use_llm=true")
    print("=" * 80)
