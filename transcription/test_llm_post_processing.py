"""
Testes para o serviço de pós-processamento com LLM
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from transcription.post_processing import LLMPostProcessingService, ProcessedSegment


class TestLLMPostProcessingService(unittest.TestCase):
    """Testes para pós-processamento com LLM"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.llm_service = LLMPostProcessingService(
            model_name="qwen3:30b",
            ollama_url="http://localhost:11434/api/generate"
        )
        
        self.sample_segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'ola tudo bem', 'confidence': 0.9},
            {'start': 2.5, 'end': 4.0, 'text': 'sim e voce', 'confidence': 0.95}
        ]
        
        self.sample_raw_text = 'ola tudo bem sim e voce'
    
    def test_initialization(self):
        """Testa inicialização do serviço"""
        self.assertEqual(self.llm_service.model_name, "qwen3:30b")
        self.assertEqual(self.llm_service.ollama_url, "http://localhost:11434/api/generate")
    
    def test_build_prompt_all_options(self):
        """Testa construção de prompt com todas as opções habilitadas"""
        prompt = self.llm_service._build_prompt(
            raw_text="teste de texto",
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        self.assertIn("gramática", prompt.lower())
        self.assertIn("hesitações", prompt.lower())
        self.assertIn("interlocutores", prompt.lower())
        self.assertIn("teste de texto", prompt)
    
    def test_build_prompt_only_grammar(self):
        """Testa construção de prompt apenas com correção gramatical"""
        prompt = self.llm_service._build_prompt(
            raw_text="teste",
            identify_speakers=False,
            correct_grammar=True,
            clean_hesitations=False
        )
        
        self.assertIn("gramática", prompt.lower())
        self.assertNotIn("interlocutores", prompt.lower())
    
    @patch('transcription.post_processing.requests.post')
    def test_process_transcription_success(self, mock_post):
        """Testa processamento bem-sucedido com LLM"""
        # Mock da resposta do Ollama
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Olá, tudo bem? Sim, e você?'
        }
        mock_post.return_value = mock_response
        
        corrected_text, processed_segments = self.llm_service.process_transcription(
            segments=self.sample_segments,
            raw_text=self.sample_raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        # Verificações
        self.assertIsInstance(corrected_text, str)
        self.assertTrue(len(corrected_text) > 0)
        self.assertIsInstance(processed_segments, list)
        self.assertEqual(len(processed_segments), 2)
        
        # Verificar que a chamada foi feita corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://localhost:11434/api/generate")
        
        payload = call_args[1]['json']
        self.assertEqual(payload['model'], "qwen3:30b")
        self.assertIn('prompt', payload)
        self.assertFalse(payload['stream'])
    
    @patch('transcription.post_processing.requests.post')
    def test_process_transcription_with_speaker_markers(self, mock_post):
        """Testa processamento com marcadores de interlocutores"""
        # Mock da resposta com marcadores de interlocutores
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Pessoa 1: Olá, tudo bem?\nPessoa 2: Sim, e você?'
        }
        mock_post.return_value = mock_response
        
        corrected_text, processed_segments = self.llm_service.process_transcription(
            segments=self.sample_segments,
            raw_text=self.sample_raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        # Verificar que interlocutores foram identificados
        self.assertIn('Pessoa', corrected_text)
        self.assertTrue(any(seg.speaker_id is not None for seg in processed_segments))
    
    @patch('transcription.post_processing.requests.post')
    def test_process_transcription_api_error(self, mock_post):
        """Testa tratamento de erro na API"""
        # Mock de erro na API
        mock_post.side_effect = Exception("Connection error")
        
        corrected_text, processed_segments = self.llm_service.process_transcription(
            segments=self.sample_segments,
            raw_text=self.sample_raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        # Deve retornar texto original em caso de erro
        self.assertEqual(corrected_text, self.sample_raw_text)
        self.assertEqual(len(processed_segments), 2)
        
        # Verificar que segmentos foram criados com texto original
        for i, seg in enumerate(processed_segments):
            self.assertEqual(seg.original_text, self.sample_segments[i]['text'])
            self.assertEqual(seg.corrected_text, self.sample_segments[i]['text'])
    
    def test_map_to_segments_without_speakers(self):
        """Testa mapeamento de segmentos sem identificação de interlocutores"""
        corrected_text = "Olá, tudo bem?\nSim, e você?"
        
        processed_segments = self.llm_service._map_to_segments(
            segments=self.sample_segments,
            corrected_text=corrected_text,
            identify_speakers=False
        )
        
        self.assertEqual(len(processed_segments), 2)
        self.assertIsNone(processed_segments[0].speaker_id)
        self.assertIsNone(processed_segments[1].speaker_id)
    
    def test_parse_speaker_segments(self):
        """Testa parsing de segmentos com marcadores de interlocutores"""
        corrected_text = "Pessoa 1: Olá\nPessoa 2: Oi"
        
        processed_segments = self.llm_service._parse_speaker_segments(
            segments=self.sample_segments,
            corrected_text=corrected_text
        )
        
        self.assertEqual(len(processed_segments), 2)
        self.assertIsNotNone(processed_segments[0].speaker_id)
        self.assertIn('Pessoa', processed_segments[0].speaker_id or '')
    
    def test_parse_speaker_segments_different_formats(self):
        """Testa parsing com diferentes formatos de marcadores"""
        test_cases = [
            ("Interlocutor 1: texto\nInterlocutor 2: outro", "Interlocutor 1"),
            ("Speaker A: texto\nSpeaker B: outro", "Speaker A"),
            ("Falante 1: texto\nFalante 2: outro", "Falante 1")
        ]
        
        for corrected_text, expected_speaker in test_cases:
            processed_segments = self.llm_service._parse_speaker_segments(
                segments=self.sample_segments,
                corrected_text=corrected_text
            )
            
            self.assertEqual(processed_segments[0].speaker_id, expected_speaker)
    
    def test_process_empty_segments(self):
        """Testa processamento com segmentos vazios"""
        corrected_text, processed_segments = self.llm_service.process_transcription(
            segments=[],
            raw_text="",
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        self.assertEqual(corrected_text, "")
        self.assertEqual(len(processed_segments), 0)
    
    @patch('transcription.post_processing.requests.post')
    def test_process_transcription_timeout(self, mock_post):
        """Testa tratamento de timeout"""
        mock_post.side_effect = TimeoutError("Request timeout")
        
        corrected_text, processed_segments = self.llm_service.process_transcription(
            segments=self.sample_segments,
            raw_text=self.sample_raw_text,
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        # Deve retornar texto original em caso de timeout
        self.assertEqual(corrected_text, self.sample_raw_text)
        self.assertEqual(len(processed_segments), 2)


class TestLLMIntegration(unittest.TestCase):
    """Testes de integração do LLM com outros componentes"""
    
    @patch('transcription.post_processing.requests.post')
    def test_full_pipeline_with_llm(self, mock_post):
        """Testa pipeline completo com LLM"""
        # Mock da resposta
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Pessoa 1: Olá, tudo bem? Pessoa 2: Sim, estou bem.'
        }
        mock_post.return_value = mock_response
        
        llm_service = LLMPostProcessingService(model_name="qwen3:30b")
        
        segments = [
            {'start': 0.0, 'end': 2.0, 'text': 'ola tudo bem', 'confidence': 0.9},
            {'start': 2.5, 'end': 4.5, 'text': 'sim to bem', 'confidence': 0.95}
        ]
        
        corrected_text, processed_segments = llm_service.process_transcription(
            segments=segments,
            raw_text='ola tudo bem sim to bem',
            identify_speakers=True,
            correct_grammar=True,
            clean_hesitations=True
        )
        
        # Verificações do resultado
        self.assertIn('Pessoa', corrected_text)
        self.assertTrue(len(processed_segments) > 0)
        
        # Verificar que timestamps foram preservados
        self.assertEqual(processed_segments[0].start, 0.0)
        self.assertEqual(processed_segments[0].end, 2.0)


if __name__ == '__main__':
    unittest.main()
