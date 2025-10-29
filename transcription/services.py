"""
Serviço de processamento de áudio e transcrição usando Whisper
"""
import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict

import whisper
import torch
from pydub import AudioSegment
from django.conf import settings

from .schemas import (
    TranscriptionResult,
    TranscriptionSegment,
    AudioInfo,
    TranscriptionResponse
)
from .portuguese_processor import PortugueseBRTextProcessor
from .video_processor import VideoProcessor, MediaTypeDetector

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Processa e converte arquivos de áudio para formato compatível com Whisper"""

    # Mapeamento de formatos para conversão
    FORMAT_MAPPING = {
        'opus': 'ogg',
        'm4a': 'mp4',
        'aac': 'mp4',
    }

    @staticmethod
    def get_audio_info(file_path: str) -> AudioInfo:
        """Extrai informações do arquivo de áudio"""
        try:
            audio = AudioSegment.from_file(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            return AudioInfo(
                format=Path(file_path).suffix.lstrip('.'),
                duration=len(audio) / 1000.0,  # Converter para segundos
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                file_size_mb=round(file_size_mb, 2)
            )
        except Exception as e:
            logger.error(f"Erro ao extrair info do áudio: {e}")
            raise

    @staticmethod
    def validate_audio_file(file_path: str, max_size_mb: int = None) -> Tuple[bool, Optional[str]]:
        """
        Valida arquivo de áudio

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if max_size_mb is None:
            max_size_mb = settings.MAX_AUDIO_SIZE_MB

        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            return False, "Arquivo não encontrado"

        # Verificar tamanho
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {max_size_mb}MB)"

        # Verificar formato
        extension = Path(file_path).suffix.lstrip('.').lower()
        if extension not in settings.SUPPORTED_AUDIO_FORMATS:
            return False, f"Formato '{extension}' não suportado"

        return True, None

    @staticmethod
    def convert_to_wav(input_path: str, output_path: str) -> str:
        """
        Converte áudio para formato WAV otimizado para Whisper

        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída

        Returns:
            str: Caminho do arquivo convertido
        """
        try:
            logger.info(f"Convertendo {input_path} para WAV...")

            # Carregar áudio
            audio = AudioSegment.from_file(input_path)

            # Converter para mono se necessário
            if audio.channels > 1:
                audio = audio.set_channels(1)

            # Normalizar sample rate para 16kHz (otimizado para Whisper)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)

            # Exportar como WAV
            audio.export(
                output_path,
                format='wav',
                parameters=['-ar', '16000', '-ac', '1']
            )

            logger.info(f"Conversão concluída: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao converter áudio: {e}")
            raise ValueError(f"Falha na conversão do áudio: {str(e)}")

    @staticmethod
    def extract_audio_from_video(video_path: str, output_path: str) -> str:
        """
        Extrai áudio de arquivo de vídeo (útil para Instagram .mp4)

        Args:
            video_path: Caminho do arquivo de vídeo
            output_path: Caminho do arquivo de áudio de saída

        Returns:
            str: Caminho do arquivo de áudio extraído
        """
        try:
            logger.info(f"Extraindo áudio de vídeo: {video_path}")

            audio = AudioSegment.from_file(video_path, format='mp4')

            # Converter para mono 16kHz
            audio = audio.set_channels(1).set_frame_rate(16000)

            audio.export(
                output_path,
                format='wav',
                parameters=['-ar', '16000', '-ac', '1']
            )

            logger.info(f"Áudio extraído: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao extrair áudio do vídeo: {e}")
            raise ValueError(f"Falha na extração de áudio: {str(e)}")


class WhisperTranscriber:
    """Gerencia carregamento do modelo Whisper e transcrição"""

    _model = None
    _current_model_name = None
    _device = None

    @classmethod
    def get_device(cls) -> str:
        """
        Detecta e retorna o dispositivo disponível (cuda/cpu)
        
        Returns:
            str: 'cuda' se GPU disponível, 'cpu' caso contrário
        """
        if cls._device is None:
            cls._device = "cuda" if torch.cuda.is_available() else "cpu"
            
            if cls._device == "cuda":
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"GPU detectada: {gpu_name} ({gpu_memory:.1f}GB VRAM)")
            else:
                logger.info("GPU não disponível, usando CPU")
                
        return cls._device

    @classmethod
    def load_model(cls, model_name: Optional[str] = None) -> whisper.Whisper:
        """
        Carrega modelo Whisper (singleton) no dispositivo apropriado

        Args:
            model_name: Nome do modelo (tiny, base, small, medium, large)

        Returns:
            whisper.Whisper: Modelo carregado
        """
        if model_name is None:
            model_name = settings.WHISPER_MODEL

        device = cls.get_device()

        # Reutilizar modelo se já estiver carregado
        if cls._model is not None and cls._current_model_name == model_name:
            logger.info(f"Reutilizando modelo Whisper: {model_name} ({device})")
            return cls._model

        logger.info(f"Carregando modelo Whisper: {model_name} no dispositivo: {device}")
        start_time = time.time()

        try:
            cls._model = whisper.load_model(model_name, device=device)
            cls._current_model_name = model_name

            load_time = time.time() - start_time
            logger.info(f"Modelo carregado em {load_time:.2f}s")
            
            # Log de memória GPU se disponível
            if device == "cuda":
                memory_allocated = torch.cuda.memory_allocated(0) / (1024**3)
                logger.info(f"Memória GPU alocada: {memory_allocated:.2f}GB")

            return cls._model

        except Exception as e:
            logger.error(f"Erro ao carregar modelo Whisper: {e}")
            raise RuntimeError(f"Falha ao carregar modelo: {str(e)}")

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        language: str = None,
        model_name: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcreve arquivo de áudio

        Args:
            audio_path: Caminho do arquivo de áudio (WAV 16kHz)
            language: Código do idioma (padrão: português brasileiro)
            model_name: Nome do modelo Whisper (opcional)

        Returns:
            TranscriptionResult: Resultado da transcrição
        """
        # Usar português como padrão
        if language is None:
            language = settings.WHISPER_LANGUAGE
        
        model = cls.load_model(model_name)

        logger.info(f"Transcrevendo áudio: {audio_path} (idioma: {language})")
        start_time = time.time()

        try:
            # Transcrever com Whisper
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                fp16=torch.cuda.is_available()  # Usar FP16 em GPU para economizar memória
            )

            # Processar segmentos
            segments = []
            for seg in result.get('segments', []):
                text = seg['text'].strip()
                
                # Aplicar pós-processamento de português se idioma é português
                if language == 'pt':
                    text = PortugueseBRTextProcessor.process(text)
                
                segments.append(TranscriptionSegment(
                    start=seg['start'],
                    end=seg['end'],
                    text=text,
                    confidence=seg.get('no_speech_prob', None)
                ))

            # Processar texto completo
            full_text = result['text'].strip()
            if language == 'pt':
                full_text = PortugueseBRTextProcessor.process(full_text)

            transcription_time = time.time() - start_time
            logger.info(f"Transcrição concluída em {transcription_time:.2f}s")

            return TranscriptionResult(
                text=full_text,
                segments=segments,
                language=result.get('language', language),
                duration=result.get('duration', 0)
            )

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            raise RuntimeError(f"Falha na transcrição: {str(e)}")


class TranscriptionService:
    """Serviço principal de transcrição - orquestra todo o processo"""

    @staticmethod
    def generate_cache_key(file_path: str) -> str:
        """Gera chave de cache baseada no hash do arquivo"""
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash

    @staticmethod
    def process_audio_file(
        file_path: str,
        language: str = None,
        model: Optional[str] = None
    ) -> TranscriptionResponse:
        """
        Processa arquivo de áudio ou vídeo completo

        Args:
            file_path: Caminho do arquivo de áudio ou vídeo
            language: Idioma para transcrição (padrão: português brasileiro)
            model: Modelo Whisper a usar

        Returns:
            TranscriptionResponse: Resposta completa da transcrição
        """
        # Usar português como padrão
        if language is None:
            language = settings.WHISPER_LANGUAGE
        
        start_time = time.time()
        temp_wav_path = None
        extension = Path(file_path).suffix.lstrip('.').lower()

        try:
            # Detectar se é vídeo
            is_video = extension in settings.SUPPORTED_VIDEO_FORMATS
            
            if is_video:
                logger.info(f"Arquivo de vídeo detectado: {extension}")
                
                # Validar vídeo
                is_valid, error_msg = VideoProcessor.validate_video_file(file_path)
                if not is_valid:
                    return TranscriptionResponse(
                        success=False,
                        transcription=None,
                        processing_time=time.time() - start_time,
                        audio_info=None,
                        error=error_msg or "Arquivo de vídeo inválido"
                    )
                
                # Obter informações do vídeo
                video_info = VideoProcessor.get_video_info(file_path)
                logger.info(f"Informações do vídeo: {video_info}")
                
                # Extrair áudio do vídeo
                temp_wav_path = os.path.join(
                    settings.TEMP_AUDIO_DIR,
                    f"video_extract_{int(time.time())}_{os.getpid()}.wav"
                )
                
                success, result_msg = VideoProcessor.extract_audio(
                    file_path,
                    temp_wav_path,
                    timeout=1800  # 30 minutos para vídeos grandes
                )
                
                if not success:
                    return TranscriptionResponse(
                        success=False,
                        transcription=None,
                        processing_time=time.time() - start_time,
                        audio_info=None,
                        error=f"Erro ao extrair áudio: {result_msg}"
                    )
                
                transcribe_path = temp_wav_path
                
                # Criar AudioInfo a partir do vídeo
                video_duration = 0
                if video_info and isinstance(video_info, dict):
                    video_duration = video_info.get('duration', 0)
                
                audio_info = AudioInfo(
                    format=extension,
                    duration=float(video_duration),
                    sample_rate=16000,
                    channels=1,
                    file_size_mb=os.path.getsize(file_path) / (1024 * 1024)
                )
            else:
                # Arquivo de áudio padrão
                # Validar arquivo
                is_valid, error_msg = AudioProcessor.validate_audio_file(file_path)
                if not is_valid:
                    return TranscriptionResponse(
                        success=False,
                        transcription=None,
                        processing_time=time.time() - start_time,
                        audio_info=None,
                        error=error_msg
                    )

                # Obter informações do áudio original
                audio_info = AudioProcessor.get_audio_info(file_path)

                # Converter para WAV se necessário
                if extension != 'wav':
                    temp_wav_path = os.path.join(
                        settings.TEMP_AUDIO_DIR,
                        f"temp_{int(time.time())}_{os.getpid()}.wav"
                    )

                    if extension == 'mp4':
                        # Extrair áudio de vídeo (arquivo mp4 tratado como áudio)
                        AudioProcessor.extract_audio_from_video(
                            file_path, temp_wav_path)
                    else:
                        # Converter formato de áudio
                        AudioProcessor.convert_to_wav(file_path, temp_wav_path)

                    transcribe_path = temp_wav_path
                else:
                    transcribe_path = file_path

            # Transcrever
            transcription = WhisperTranscriber.transcribe(
                transcribe_path,
                language=language,
                model_name=model
            )

            processing_time = time.time() - start_time

            return TranscriptionResponse(
                success=True,
                transcription=transcription,
                processing_time=round(processing_time, 2),
                audio_info=audio_info,
                error=None
            )

        except Exception as e:
            logger.error(f"Erro no processamento: {e}", exc_info=True)
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=str(e)
            )

        finally:
            # Limpar arquivo temporário
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    logger.info(
                        f"Arquivo temporário removido: {temp_wav_path}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário: {e}")
