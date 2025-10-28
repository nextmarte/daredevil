"""
Serviço de pós-processamento de transcrição
Corrige gramática, pontuação e identifica interlocutores
"""
import re
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

import language_tool_python

logger = logging.getLogger(__name__)


@dataclass
class Speaker:
    """Representa um interlocutor identificado"""
    id: str
    name: Optional[str] = None
    segments: List[int] = None  # Índices dos segmentos do interlocutor
    
    def __post_init__(self):
        if self.segments is None:
            self.segments = []


@dataclass
class ProcessedSegment:
    """Segmento processado com texto corrigido e interlocutor"""
    start: float
    end: float
    original_text: str
    corrected_text: str
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None


class GrammarCorrector:
    """Corrige gramática e pontuação em português"""
    
    _tool = None
    
    @classmethod
    def get_tool(cls):
        """Obtém instância singleton do LanguageTool"""
        if cls._tool is None:
            logger.info("Inicializando LanguageTool para português...")
            try:
                cls._tool = language_tool_python.LanguageTool('pt-BR')
                logger.info("LanguageTool inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar LanguageTool: {e}")
                # Tentar com pt genérico
                try:
                    cls._tool = language_tool_python.LanguageTool('pt')
                    logger.info("LanguageTool inicializado com pt genérico")
                except Exception as e2:
                    logger.error(f"Erro ao inicializar LanguageTool com pt: {e2}")
                    raise RuntimeError("Não foi possível inicializar corretor gramatical")
        return cls._tool
    
    @classmethod
    def correct_text(cls, text: str, fix_capitalization: bool = True) -> str:
        """
        Corrige gramática e pontuação de um texto
        
        Args:
            text: Texto a ser corrigido
            fix_capitalization: Se deve corrigir capitalização
            
        Returns:
            str: Texto corrigido
        """
        if not text or not text.strip():
            return text
        
        try:
            tool = cls.get_tool()
            
            # Aplicar correções
            corrected = tool.correct(text)
            
            # Capitalizar primeira letra se necessário
            if fix_capitalization and corrected:
                corrected = corrected[0].upper() + corrected[1:] if len(corrected) > 1 else corrected.upper()
            
            return corrected
            
        except Exception as e:
            logger.warning(f"Erro ao corrigir texto: {e}. Retornando texto original.")
            return text
    
    @classmethod
    def clean_hesitations(cls, text: str) -> str:
        """
        Remove hesitações comuns da fala em português
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            str: Texto sem hesitações
        """
        # Padrões comuns de hesitação em português
        hesitations = [
            r'\bé+\b',  # é, éé, ééé
            r'\bah+\b',  # ah, ahh
            r'\boh+\b',  # oh, ohh
            r'\buh+m*\b',  # uh, uhm, uhmm
            r'\ber+\b',  # er, err
            r'\bhm+\b',  # hm, hmm
            r'\bn[eé]+\b',  # né, nee
        ]
        
        cleaned = text
        for pattern in hesitations:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remover espaços múltiplos
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()


class SpeakerIdentifier:
    """Identifica interlocutores baseado em padrões de conversa"""
    
    @staticmethod
    def identify_speakers(segments: List[Dict]) -> List[ProcessedSegment]:
        """
        Identifica interlocutores baseado em pausas e padrões de conversa
        
        Args:
            segments: Lista de segmentos com start, end, text
            
        Returns:
            List[ProcessedSegment]: Segmentos com identificação de interlocutor
        """
        if not segments:
            return []
        
        processed_segments = []
        speaker_ids = ["Speaker_A", "Speaker_B", "Speaker_C", "Speaker_D"]
        speaker_index = 0
        current_speaker_id = speaker_ids[speaker_index]
        
        for i, segment in enumerate(segments):
            text = segment.get('text', '').strip()
            should_change_speaker = False
            
            if i > 0:
                prev_segment = segments[i - 1]
                prev_text = prev_segment.get('text', '').strip()
                pause_duration = segment.get('start', 0) - prev_segment.get('end', 0)
                
                # Critério 1: Pausa maior que 1.0 segundo
                if pause_duration > 1.0:
                    should_change_speaker = True
                
                # Critério 2: Pergunta seguida de afirmação ou vice-versa
                is_current_question = SpeakerIdentifier._is_question(text)
                is_prev_question = SpeakerIdentifier._is_question(prev_text)
                
                if is_current_question != is_prev_question:
                    should_change_speaker = True
                
                # Critério 3: Pergunta após pergunta também indica mudança
                elif is_current_question and is_prev_question:
                    should_change_speaker = True
            
            # Mudar de interlocutor se necessário
            if should_change_speaker:
                speaker_index = (speaker_index + 1) % len(speaker_ids)
                current_speaker_id = speaker_ids[speaker_index]
            
            processed_segments.append(ProcessedSegment(
                start=segment.get('start', 0),
                end=segment.get('end', 0),
                original_text=text,
                corrected_text=text,  # Será corrigido depois
                speaker_id=current_speaker_id,
                confidence=segment.get('confidence')
            ))
        
        return processed_segments
    
    @staticmethod
    def _is_question(text: str) -> bool:
        """Detecta se o texto é uma pergunta"""
        if not text:
            return False
        
        # Termina com ponto de interrogação
        if text.strip().endswith('?'):
            return True
        
        # Começa com palavra interrogativa
        question_words = [
            'quem', 'o que', 'quando', 'onde', 'por que', 'porque',
            'qual', 'quais', 'quanto', 'quantos', 'como', 'cadê'
        ]
        
        text_lower = text.lower()
        for word in question_words:
            if text_lower.startswith(word):
                return True
        
        return False


class PostProcessingService:
    """Serviço principal de pós-processamento"""
    
    @staticmethod
    def process_transcription(
        segments: List[Dict],
        correct_grammar: bool = True,
        identify_speakers: bool = True,
        clean_hesitations: bool = True
    ) -> Tuple[str, List[ProcessedSegment]]:
        """
        Processa transcrição completa
        
        Args:
            segments: Lista de segmentos da transcrição
            correct_grammar: Se deve corrigir gramática
            identify_speakers: Se deve identificar interlocutores
            clean_hesitations: Se deve remover hesitações
            
        Returns:
            Tuple[str, List[ProcessedSegment]]: Texto completo corrigido e segmentos processados
        """
        if not segments:
            return "", []
        
        # Identificar interlocutores se solicitado
        if identify_speakers:
            processed_segments = SpeakerIdentifier.identify_speakers(segments)
        else:
            processed_segments = [
                ProcessedSegment(
                    start=seg.get('start', 0),
                    end=seg.get('end', 0),
                    original_text=seg.get('text', ''),
                    corrected_text=seg.get('text', ''),
                    speaker_id=None,
                    confidence=seg.get('confidence')
                )
                for seg in segments
            ]
        
        # Processar cada segmento
        full_text_parts = []
        
        for i, processed_seg in enumerate(processed_segments):
            text = processed_seg.original_text
            
            # Limpar hesitações se solicitado
            if clean_hesitations:
                text = GrammarCorrector.clean_hesitations(text)
            
            # Corrigir gramática se solicitado
            if correct_grammar:
                try:
                    text = GrammarCorrector.correct_text(text)
                except Exception as e:
                    logger.warning(f"Erro ao corrigir segmento {i}: {e}")
            
            # Atualizar segmento processado
            processed_seg.corrected_text = text
            
            # Adicionar ao texto completo com identificação de interlocutor
            if identify_speakers and processed_seg.speaker_id:
                # Adicionar marcador de interlocutor se mudou
                if i == 0 or processed_segments[i-1].speaker_id != processed_seg.speaker_id:
                    full_text_parts.append(f"\n{processed_seg.speaker_id}: {text}")
                else:
                    full_text_parts.append(f" {text}")
            else:
                full_text_parts.append(f" {text}")
        
        # Juntar texto completo
        full_text = ''.join(full_text_parts).strip()
        
        return full_text, processed_segments
    
    @staticmethod
    def format_conversation(processed_segments: List[ProcessedSegment]) -> str:
        """
        Formata conversa com identificação de interlocutores
        
        Args:
            processed_segments: Segmentos processados
            
        Returns:
            str: Conversa formatada
        """
        if not processed_segments:
            return ""
        
        formatted_lines = []
        current_speaker = None
        current_text = []
        
        for seg in processed_segments:
            if seg.speaker_id != current_speaker:
                # Adicionar fala do interlocutor anterior
                if current_text:
                    formatted_lines.append(f"{current_speaker}: {' '.join(current_text)}")
                    current_text = []
                
                current_speaker = seg.speaker_id
            
            if seg.corrected_text.strip():
                current_text.append(seg.corrected_text.strip())
        
        # Adicionar última fala
        if current_text:
            formatted_lines.append(f"{current_speaker}: {' '.join(current_text)}")
        
        return '\n'.join(formatted_lines)
