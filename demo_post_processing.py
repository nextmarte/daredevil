#!/usr/bin/env python
"""
Script de exemplo para testar o pós-processamento de transcrição
Demonstra correção gramatical e identificação de interlocutores
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transcription.post_processing import PostProcessingService, SpeakerIdentifier, GrammarCorrector


def example_basic_transcription():
    """Exemplo básico de processamento de transcrição"""
    print("=" * 80)
    print("EXEMPLO 1: Processamento Básico de Transcrição")
    print("=" * 80)
    
    # Simular segmentos de uma conversa
    segments = [
        {'start': 0.0, 'end': 2.5, 'text': 'Olá, tudo bem com você?', 'confidence': 0.95},
        {'start': 3.0, 'end': 5.0, 'text': 'Sim, estou bem. E você?', 'confidence': 0.92},
        {'start': 6.0, 'end': 8.5, 'text': 'Também estou bem, obrigado.', 'confidence': 0.94},
        {'start': 9.0, 'end': 11.0, 'text': 'Qual é o assunto de hoje?', 'confidence': 0.93},
        {'start': 11.5, 'end': 14.0, 'text': 'Vamos discutir o projeto novo.', 'confidence': 0.96}
    ]
    
    # Processar sem correção gramatical (para evitar dependência de rede)
    full_text, processed_segments = PostProcessingService.process_transcription(
        segments=segments,
        correct_grammar=False,
        identify_speakers=True,
        clean_hesitations=False
    )
    
    print("\nTexto Completo:")
    print(full_text)
    
    print("\nSegmentos Processados:")
    for seg in processed_segments:
        print(f"  [{seg.start:.1f}s - {seg.end:.1f}s] {seg.speaker_id}: {seg.corrected_text}")
    
    print("\nConversa Formatada:")
    formatted = PostProcessingService.format_conversation(processed_segments)
    print(formatted)


def example_with_hesitations():
    """Exemplo com remoção de hesitações"""
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Remoção de Hesitações")
    print("=" * 80)
    
    # Segmentos com hesitações
    segments = [
        {'start': 0.0, 'end': 3.0, 'text': 'Olá, é, como vai você ah hoje?', 'confidence': 0.88},
        {'start': 3.5, 'end': 6.0, 'text': 'Estou bem, er, obrigado por perguntar.', 'confidence': 0.90}
    ]
    
    print("\nTexto Original:")
    for seg in segments:
        print(f"  - {seg['text']}")
    
    # Processar com remoção de hesitações
    full_text, processed_segments = PostProcessingService.process_transcription(
        segments=segments,
        correct_grammar=False,
        identify_speakers=False,
        clean_hesitations=True
    )
    
    print("\nTexto Após Remoção de Hesitações:")
    for seg in processed_segments:
        print(f"  - {seg.corrected_text}")


def example_speaker_detection():
    """Exemplo de detecção de interlocutores"""
    print("\n" + "=" * 80)
    print("EXEMPLO 3: Detecção de Interlocutores")
    print("=" * 80)
    
    # Conversa com múltiplos interlocutores
    segments = [
        {'start': 0.0, 'end': 1.5, 'text': 'Bom dia!', 'confidence': 0.95},
        {'start': 2.5, 'end': 4.0, 'text': 'Bom dia! Como você está?', 'confidence': 0.93},
        {'start': 5.0, 'end': 6.5, 'text': 'Estou bem.', 'confidence': 0.94},
        {'start': 7.0, 'end': 9.0, 'text': 'Ótimo! Vamos começar?', 'confidence': 0.92},
        {'start': 9.5, 'end': 10.5, 'text': 'Sim, vamos.', 'confidence': 0.95}
    ]
    
    processed_segments = SpeakerIdentifier.identify_speakers(segments)
    
    print("\nInterlocutores Identificados:")
    for seg in processed_segments:
        print(f"  [{seg.start:.1f}s - {seg.end:.1f}s] {seg.speaker_id}: {seg.original_text}")
    
    # Contar interlocutores únicos
    speakers = set(seg.speaker_id for seg in processed_segments)
    print(f"\nTotal de interlocutores detectados: {len(speakers)}")
    print(f"Interlocutores: {', '.join(sorted(speakers))}")


def example_question_detection():
    """Exemplo de detecção de perguntas"""
    print("\n" + "=" * 80)
    print("EXEMPLO 4: Detecção de Perguntas")
    print("=" * 80)
    
    test_texts = [
        "Como você está?",
        "Quem é você?",
        "Onde fica o escritório?",
        "Por que isso aconteceu?",
        "Estou bem, obrigado.",
        "O projeto está pronto.",
        "qual o próximo passo"  # Sem ponto de interrogação mas começa com palavra interrogativa
    ]
    
    print("\nTestando detecção de perguntas:")
    for text in test_texts:
        is_question = SpeakerIdentifier._is_question(text)
        result = "✓ Pergunta" if is_question else "✗ Não é pergunta"
        print(f"  {result}: \"{text}\"")


def example_clean_hesitations():
    """Exemplo de limpeza de hesitações"""
    print("\n" + "=" * 80)
    print("EXEMPLO 5: Limpeza de Hesitações")
    print("=" * 80)
    
    test_texts = [
        "Olá, é, eu queria ah falar sobre er o projeto",
        "Hmm, eu acho que né isso está certo",
        "Uh, deixa eu ver uhm o documento"
    ]
    
    print("\nLimpando hesitações:")
    for text in test_texts:
        cleaned = GrammarCorrector.clean_hesitations(text)
        print(f"  Original: {text}")
        print(f"  Limpo:    {cleaned}")
        print()


if __name__ == '__main__':
    print("\n" + "🎙️ " * 20)
    print("DEMONSTRAÇÃO DO SISTEMA DE PÓS-PROCESSAMENTO DE TRANSCRIÇÃO")
    print("🎙️ " * 20 + "\n")
    
    # Executar exemplos
    example_basic_transcription()
    example_with_hesitations()
    example_speaker_detection()
    example_question_detection()
    example_clean_hesitations()
    
    print("\n" + "=" * 80)
    print("✅ Demonstração concluída!")
    print("=" * 80)
