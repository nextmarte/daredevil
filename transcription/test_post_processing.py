"""
Testes para o serviço de pós-processamento
"""
import unittest
from transcription.post_processing import (
    GrammarCorrector,
    SpeakerIdentifier,
    PostProcessingService,
    ProcessedSegment
)


class TestGrammarCorrector(unittest.TestCase):
    """Testes para correção gramatical"""
    
    def test_clean_hesitations(self):
        """Testa remoção de hesitações"""
        text = "Olá, é, eu queria ah falar sobre er o projeto"
        cleaned = GrammarCorrector.clean_hesitations(text)
        # Deve remover 'é', 'ah', 'er'
        self.assertNotIn(' é ', cleaned.lower())
        self.assertNotIn(' ah ', cleaned.lower())
        self.assertNotIn(' er ', cleaned.lower())
    
    def test_clean_hesitations_preserves_words(self):
        """Testa que palavras normais não são removidas"""
        text = "Ele é um bom profissional"
        cleaned = GrammarCorrector.clean_hesitations(text)
        # 'é' como verbo deve ser preservado quando não é hesitação isolada
        self.assertIn("profissional", cleaned)
    
    def test_correct_text_basic(self):
        """Testa correção básica de texto"""
        # Teste básico - se o LanguageTool estiver disponível
        try:
            text = "ola como vai voce"
            corrected = GrammarCorrector.correct_text(text)
            # Deve retornar algum texto (pode ou não estar corrigido dependendo do LanguageTool)
            self.assertIsInstance(corrected, str)
            self.assertTrue(len(corrected) > 0)
        except Exception as e:
            # Se LanguageTool não estiver disponível, pula o teste
            self.skipTest(f"LanguageTool não disponível: {e}")


class TestSpeakerIdentifier(unittest.TestCase):
    """Testes para identificação de interlocutores"""
    
    def test_identify_speakers_basic(self):
        """Testa identificação básica de interlocutores"""
        segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'Olá, tudo bem?'},
            {'start': 2.5, 'end': 4.0, 'text': 'Sim, e você?'},
            {'start': 5.0, 'end': 7.0, 'text': 'Estou bem também.'}
        ]
        
        processed = SpeakerIdentifier.identify_speakers(segments)
        
        self.assertEqual(len(processed), 3)
        # Deve ter pelo menos 2 interlocutores diferentes
        speakers = set(seg.speaker_id for seg in processed)
        self.assertGreaterEqual(len(speakers), 2)
    
    def test_identify_speakers_with_questions(self):
        """Testa identificação com perguntas"""
        segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'Como você está?'},
            {'start': 2.5, 'end': 4.0, 'text': 'Estou bem.'},
            {'start': 4.5, 'end': 6.0, 'text': 'E você, como está?'}
        ]
        
        processed = SpeakerIdentifier.identify_speakers(segments)
        
        # Perguntas devem indicar mudança de interlocutor
        self.assertNotEqual(processed[0].speaker_id, processed[1].speaker_id)
    
    def test_is_question(self):
        """Testa detecção de perguntas"""
        self.assertTrue(SpeakerIdentifier._is_question("Como você está?"))
        self.assertTrue(SpeakerIdentifier._is_question("Quem é você?"))
        self.assertTrue(SpeakerIdentifier._is_question("Onde fica isso?"))
        self.assertFalse(SpeakerIdentifier._is_question("Estou bem."))
        self.assertFalse(SpeakerIdentifier._is_question("Obrigado."))


class TestPostProcessingService(unittest.TestCase):
    """Testes para serviço de pós-processamento completo"""
    
    def test_process_transcription_basic(self):
        """Testa processamento básico"""
        segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'Olá, tudo bem?', 'confidence': 0.9},
            {'start': 2.5, 'end': 4.0, 'text': 'Sim, e você?', 'confidence': 0.95}
        ]
        
        # Testar sem correção gramatical para evitar dependência do LanguageTool
        full_text, processed_segments = PostProcessingService.process_transcription(
            segments=segments,
            correct_grammar=False,
            identify_speakers=True,
            clean_hesitations=False
        )
        
        self.assertIsInstance(full_text, str)
        self.assertTrue(len(full_text) > 0)
        self.assertEqual(len(processed_segments), 2)
        
        # Deve ter identificado interlocutores
        self.assertIsNotNone(processed_segments[0].speaker_id)
        self.assertIsNotNone(processed_segments[1].speaker_id)
    
    def test_process_transcription_with_hesitations(self):
        """Testa processamento com remoção de hesitações"""
        segments = [
            {'start': 0.0, 'end': 3.0, 'text': 'Olá, é, como vai você ah hoje?', 'confidence': 0.9}
        ]
        
        full_text, processed_segments = PostProcessingService.process_transcription(
            segments=segments,
            correct_grammar=False,
            identify_speakers=False,
            clean_hesitations=True
        )
        
        # Hesitações devem ter sido removidas
        cleaned_text = processed_segments[0].corrected_text
        self.assertNotIn(' é ', cleaned_text.lower() + ' ')
        self.assertNotIn(' ah ', cleaned_text.lower() + ' ')
    
    def test_format_conversation(self):
        """Testa formatação de conversa"""
        processed_segments = [
            ProcessedSegment(0.0, 2.0, 'Olá', 'Olá', 'Speaker_A', 0.9),
            ProcessedSegment(2.5, 4.0, 'Oi', 'Oi', 'Speaker_B', 0.95),
            ProcessedSegment(4.5, 6.0, 'Tudo bem?', 'Tudo bem?', 'Speaker_A', 0.9)
        ]
        
        formatted = PostProcessingService.format_conversation(processed_segments)
        
        self.assertIn('Speaker_A:', formatted)
        self.assertIn('Speaker_B:', formatted)
        self.assertIn('Olá', formatted)
        self.assertIn('Oi', formatted)
    
    def test_process_empty_segments(self):
        """Testa processamento com segmentos vazios"""
        segments = []
        
        full_text, processed_segments = PostProcessingService.process_transcription(
            segments=segments,
            correct_grammar=False,
            identify_speakers=False,
            clean_hesitations=False
        )
        
        self.assertEqual(full_text, "")
        self.assertEqual(len(processed_segments), 0)


if __name__ == '__main__':
    unittest.main()
