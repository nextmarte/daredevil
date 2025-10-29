"""
Pós-processamento de texto em português brasileiro
Melhora a qualidade da transcrição com correções específicas do idioma
"""
import re
import logging
from typing import List, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração português BR
PT_BR_CONFIG = settings.PORTUGUESE_BR_CONFIG


class PortugueseBRTextProcessor:
    """Processa e melhora texto em português brasileiro"""

    @staticmethod
    def remove_hesitations(text: str) -> str:
        """
        Remove hesitações comuns em português

        Exemplos: "hã", "hm", "tipo", "sabe", "entendeu", "né", "tá"
        """
        hesitations = PT_BR_CONFIG['hesitations']
        
        # Padrão para hesitações como palavras inteiras
        pattern = r'\b(' + '|'.join(re.escape(h) for h in hesitations) + r')\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Limpar espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """
        Normaliza pontuação de acordo com padrões portugueses

        - Remove espaços antes de pontuação
        - Corrige múltiplas pontuações
        - Adiciona espaço após pontuação
        """
        # Remover espaço antes de pontuação
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Corrigir múltiplas pontuações (ex: "..." -> "...")
        text = re.sub(r'\.{2,}', '...', text)
        text = re.sub(r'(!{2,})', '!', text)
        text = re.sub(r'(\?{2,})', '?', text)
        
        # Adicionar espaço após pontuação (exceto no final)
        text = re.sub(r'([.!?])\s*(?=[A-Za-z])', r'\1 ', text)
        
        # Corrigir espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def capitalize_properly(text: str) -> str:
        """
        Capitaliza primeira letra de frases e nomes próprios comuns

        - Primeira letra do texto
        - Primeira letra após pontuação final (., !, ?)
        - Preserva abreviações comuns
        """
        # Capitalizar primeira letra do texto
        if text:
            text = text[0].upper() + text[1:]
        
        # Capitalizar após pontuação final
        pattern = r'([.!?])\s+([a-z])'
        text = re.sub(pattern, lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
        
        # Capitalizar "de", "da", "do" após nomes (básico)
        # Nomes próprios típicos em português
        names_patterns = [
            r'\b(joão|maria|josé|carlos|paulo|francisco|ana|silva|oliveira|santos|costa)\b',
        ]
        for pattern in names_patterns:
            text = re.sub(pattern, lambda m: m.group(1).capitalize(), text, flags=re.IGNORECASE)
        
        return text

    @staticmethod
    def expand_abbreviations(text: str) -> str:
        """
        Expande abreviações comuns em português

        Exemplo: "sr" -> "Sr."
        """
        abbreviations = PT_BR_CONFIG['abbreviations']
        
        for abbr, full in abbreviations.items():
            # Substituir abreviação seguida de espaço ou pontuação
            pattern = r'\b' + re.escape(abbr) + r'(?=\s|[.,!?;:]|$)'
            text = re.sub(pattern, full, text, flags=re.IGNORECASE)
        
        return text

    @staticmethod
    def fix_common_mistakes(text: str) -> str:
        """
        Corrige erros comuns em português brasileiro
        
        - Acentuação incorreta
        - Crase mal colocada
        - Palavras mal separadas
        """
        # Corrigir alguns erros comuns do Whisper em português
        corrections = {
            # Acentuação
            r'\bé\s+(?=um)': 'É ',  # "é um" no início
            
            # Crase comum
            r'\ba\s+a\s+': 'à ',  # "a a" -> "à"
            
            # Contração comum
            r'\bde\s+o\s+': 'do ',
            r'\bde\s+a\s+': 'da ',
            r'\bem\s+o\s+': 'no ',
            r'\bem\s+a\s+': 'na ',
        }
        
        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        Limpa espaços em branco desnecessários
        """
        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        # Remover espaços antes de pontuação
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Remover espaços no início e fim
        text = text.strip()
        
        return text

    @classmethod
    def process(cls, text: str, remove_hesitations: bool = True,
                expand_abbreviations: bool = True) -> str:
        """
        Aplica processamento completo de texto em português

        Args:
            text: Texto a processar
            remove_hesitations: Se deve remover hesitações
            expand_abbreviations: Se deve expandir abreviações

        Returns:
            Texto processado
        """
        if not text:
            return text
        
        logger.debug(f"Processando texto em português BR (tamanho: {len(text)})")
        
        # Aplicar processamentos na ordem
        if remove_hesitations:
            text = cls.remove_hesitations(text)
        
        # Normalizar pontuação
        text = cls.normalize_punctuation(text)
        
        # Capitalizar
        text = cls.capitalize_properly(text)
        
        # Corrigir erros comuns
        text = cls.fix_common_mistakes(text)
        
        if expand_abbreviations:
            text = cls.expand_abbreviations(text)
        
        # Limpeza final
        text = cls.clean_whitespace(text)
        
        logger.debug(f"Texto processado (tamanho final: {len(text)})")
        
        return text

    @staticmethod
    def process_segments(segments: List[dict]) -> List[dict]:
        """
        Processa lista de segmentos de transcrição

        Args:
            segments: Lista de segmentos com texto e timestamps

        Returns:
            Segmentos com texto processado
        """
        for segment in segments:
            if 'text' in segment:
                segment['text'] = PortugueseBRTextProcessor.process(
                    segment['text'],
                    remove_hesitations=True,
                    expand_abbreviations=True
                )
        
        return segments


class LanguageDetector:
    """Detecta idioma do áudio (simples implementação)"""

    @staticmethod
    def detect_language(text_sample: str) -> Tuple[str, float]:
        """
        Detecta idioma baseado em amostra de texto

        Args:
            text_sample: Amostra de texto para análise

        Returns:
            Tupla (código_idioma, confiança)
        """
        # Palavras características de português
        pt_indicators = {
            'de', 'que', 'o', 'a', 'para', 'e', 'em', 'por',
            'são', 'está', 'você', 'ela', 'ele', 'nós', 'eles',
            'elas', 'não', 'como', 'mais', 'qual', 'quando', 'onde',
            'quem', 'será', 'com', 'sem', 'entre', 'já', 'também',
            'português', 'brasil', 'brasileira', 'brasileiro'
        }
        
        # Converter para minúsculas e separar palavras
        words = text_sample.lower().split()
        
        # Contar indicadores
        match_count = sum(1 for word in words if word in pt_indicators)
        
        # Calcular confiança
        if len(words) == 0:
            confidence = 0.0
        else:
            confidence = min(1.0, match_count / len(words))
        
        # Se confiança alta, é português
        if confidence > 0.3:
            return 'pt', confidence
        
        # Caso contrário, retornar português como padrão (já que é a configuração padrão)
        return 'pt', 0.5


def process_transcription_text(text: str) -> str:
    """
    Função conveniência para processar texto de transcrição

    Args:
        text: Texto da transcrição

    Returns:
        Texto processado em português
    """
    return PortugueseBRTextProcessor.process(text)
