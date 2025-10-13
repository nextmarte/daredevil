"""
Schemas Pydantic para validação de entrada e saída da API
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TranscriptionSegment(BaseModel):
    """Segmento individual da transcrição com timestamps"""
    start: float = Field(..., description="Tempo de início em segundos")
    end: float = Field(..., description="Tempo de fim em segundos")
    text: str = Field(..., description="Texto transcrito do segmento")
    confidence: Optional[float] = Field(None, description="Confiança da transcrição (0-1)")


class AudioInfo(BaseModel):
    """Informações sobre o arquivo de áudio processado"""
    format: str = Field(..., description="Formato do arquivo de áudio")
    duration: float = Field(..., description="Duração em segundos")
    sample_rate: int = Field(..., description="Taxa de amostragem em Hz")
    channels: int = Field(..., description="Número de canais (1=mono, 2=stereo)")
    file_size_mb: float = Field(..., description="Tamanho do arquivo em MB")


class TranscriptionResult(BaseModel):
    """Resultado detalhado da transcrição"""
    text: str = Field(..., description="Texto completo da transcrição")
    segments: List[TranscriptionSegment] = Field(
        default_factory=list,
        description="Lista de segmentos com timestamps"
    )
    language: str = Field(..., description="Idioma detectado ou configurado")
    duration: float = Field(..., description="Duração total do áudio em segundos")


class TranscriptionResponse(BaseModel):
    """Resposta completa da API de transcrição"""
    success: bool = Field(..., description="Indica se a transcrição foi bem-sucedida")
    transcription: Optional[TranscriptionResult] = Field(
        None,
        description="Resultado da transcrição se bem-sucedida"
    )
    processing_time: float = Field(..., description="Tempo de processamento em segundos")
    audio_info: Optional[AudioInfo] = Field(
        None,
        description="Informações sobre o áudio processado"
    )
    error: Optional[str] = Field(None, description="Mensagem de erro se houver falha")


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check"""
    status: str = Field(..., description="Status do serviço (healthy/unhealthy)")
    whisper_model: str = Field(..., description="Modelo Whisper carregado")
    supported_formats: List[str] = Field(..., description="Formatos de áudio suportados")
    max_file_size_mb: int = Field(..., description="Tamanho máximo de arquivo permitido")
    temp_dir: str = Field(..., description="Diretório temporário para processamento")


class BatchTranscriptionResponse(BaseModel):
    """Resposta para processamento em lote"""
    total_files: int = Field(..., description="Total de arquivos processados")
    successful: int = Field(..., description="Número de transcrições bem-sucedidas")
    failed: int = Field(..., description="Número de falhas")
    results: List[TranscriptionResponse] = Field(
        default_factory=list,
        description="Lista de resultados individuais"
    )
    total_processing_time: float = Field(..., description="Tempo total de processamento")


class TranscribeRequest(BaseModel):
    """Parâmetros opcionais para transcrição"""
    language: str = Field(default="pt", description="Código do idioma (pt, en, es, etc)")
    model: Optional[str] = Field(None, description="Modelo Whisper a usar (sobrescreve padrão)")
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Valida código de idioma"""
        valid_languages = ['pt', 'en', 'es', 'fr', 'de', 'it', 'ja', 'zh', 'ko']
        if v not in valid_languages:
            raise ValueError(f"Idioma '{v}' não suportado. Use: {', '.join(valid_languages)}")
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Valida modelo Whisper"""
        if v is None:
            return v
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if v not in valid_models:
            raise ValueError(f"Modelo '{v}' não suportado. Use: {', '.join(valid_models)}")
        return v
