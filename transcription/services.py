"""
Serviço de processamento de áudio e transcrição usando Whisper
"""
import os
import time
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict

import whisper
from pydub import AudioSegment
from django.conf import settings

from .schemas import (
    TranscriptionResult,
    TranscriptionSegment,
    AudioInfo,
    TranscriptionResponse
)
from .post_processing import PostProcessingService, LLMPostProcessingService

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
    def check_ffmpeg_installed():
        """Verifica se ffmpeg/ffprobe estão instalados"""
        if not shutil.which('ffmpeg'):
            raise RuntimeError(
                "ffmpeg não encontrado. Instale com: "
                "sudo apt-get install ffmpeg (Linux) ou brew install ffmpeg (macOS)"
            )
        if not shutil.which('ffprobe'):
            raise RuntimeError(
                "ffprobe não encontrado. Instale com: "
                "sudo apt-get install ffmpeg (Linux) ou brew install ffmpeg (macOS)"
            )

    @staticmethod
    def get_audio_info(file_path: str) -> AudioInfo:
        """Extrai informações do arquivo de áudio"""
        try:
            # Verificar dependências antes de processar
            AudioProcessor.check_ffmpeg_installed()

            audio = AudioSegment.from_file(file_path)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            return AudioInfo(
                format=Path(file_path).suffix.lstrip('.'),
                duration=len(audio) / 1000.0,  # Converter para segundos
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                file_size_mb=round(file_size_mb, 2)
            )
        except RuntimeError as e:
            # Re-raise erros de dependências
            raise
        except Exception as e:
            logger.error(f"Erro ao extrair info do áudio: {e}")
            # Retornar info básica se falhar
            return AudioInfo(
                format='wav',
                duration=0,
                sample_rate=16000,
                channels=1,
                file_size_mb=0
            )

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

    @classmethod
    def load_model(cls, model_name: Optional[str] = None) -> whisper.Whisper:
        """
        Carrega modelo Whisper (singleton)

        Args:
            model_name: Nome do modelo (tiny, base, small, medium, large)

        Returns:
            whisper.Whisper: Modelo carregado
        """
        if model_name is None:
            model_name = settings.WHISPER_MODEL

        # Reutilizar modelo se já estiver carregado
        if cls._model is not None and cls._current_model_name == model_name:
            logger.info(f"Reutilizando modelo Whisper: {model_name}")
            return cls._model

        logger.info(f"Carregando modelo Whisper: {model_name}")
        start_time = time.time()

        try:
            cls._model = whisper.load_model(model_name)
            cls._current_model_name = model_name

            load_time = time.time() - start_time
            logger.info(f"Modelo carregado em {load_time:.2f}s")

            return cls._model

        except Exception as e:
            logger.error(f"Erro ao carregar modelo Whisper: {e}")
            raise RuntimeError(f"Falha ao carregar modelo: {str(e)}")

    @classmethod
    def transcribe(
        cls,
        audio_path: str,
        language: str = "pt",
        model_name: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcreve arquivo de áudio

        Args:
            audio_path: Caminho do arquivo de áudio (WAV 16kHz)
            language: Código do idioma
            model_name: Nome do modelo Whisper (opcional)

        Returns:
            TranscriptionResult: Resultado da transcrição
        """
        model = cls.load_model(model_name)

        logger.info(f"Transcrevendo áudio: {audio_path} (idioma: {language})")
        start_time = time.time()

        try:
            # Transcrever com Whisper
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )

            # Processar segmentos
            segments = []
            for seg in result.get('segments', []):
                segments.append(TranscriptionSegment(
                    start=seg['start'],
                    end=seg['end'],
                    text=seg['text'].strip(),
                    confidence=seg.get('no_speech_prob', None)
                ))

            transcription_time = time.time() - start_time
            logger.info(f"Transcrição concluída em {transcription_time:.2f}s")

            return TranscriptionResult(
                text=result['text'].strip(),
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
        language: str = "pt",
        model: Optional[str] = None,
        post_process: bool = True,
        correct_grammar: bool = True,
        identify_speakers: bool = True,
        clean_hesitations: bool = True,
        use_llm: bool = None
    ) -> TranscriptionResponse:
        """
        Processa arquivo de áudio completo

        Args:
            file_path: Caminho do arquivo de áudio
            language: Idioma para transcrição
            model: Modelo Whisper a usar
            post_process: Se deve aplicar pós-processamento
            correct_grammar: Se deve corrigir gramática (requer post_process=True)
            identify_speakers: Se deve identificar interlocutores (requer post_process=True)
            clean_hesitations: Se deve remover hesitações (requer post_process=True)
            use_llm: Se deve usar LLM (Qwen3:30b) para pós-processamento (None = usar config do settings)

        Returns:
            TranscriptionResponse: Resposta completa da transcrição
        """
        start_time = time.time()
        temp_wav_path = None

        try:
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
            extension = Path(file_path).suffix.lstrip('.').lower()
            if extension != 'wav':
                temp_wav_path = os.path.join(
                    settings.TEMP_AUDIO_DIR,
                    f"temp_{int(time.time())}_{os.getpid()}.wav"
                )

                if extension == 'mp4':
                    # Extrair áudio de vídeo
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
            
            # Aplicar pós-processamento se habilitado
            if post_process and language in ['pt', 'pt-BR']:
                try:
                    logger.info("Aplicando pós-processamento...")
                    
                    # Preparar segmentos para pós-processamento
                    segments_dict = [
                        {
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text,
                            'confidence': seg.confidence
                        }
                        for seg in transcription.segments
                    ]
                    
                    # Determinar se deve usar LLM
                    if use_llm is None:
                        use_llm = settings.USE_LLM_POST_PROCESSING
                    
                    if use_llm:
                        # Usar LLM para pós-processamento
                        logger.info(f"Usando LLM ({settings.LLM_MODEL}) para pós-processamento...")
                        llm_service = LLMPostProcessingService(
                            model_name=settings.LLM_MODEL,
                            ollama_host=settings.OLLAMA_HOST
                        )
                        
                        corrected_text, processed_segments = llm_service.process_transcription(
                            segments=segments_dict,
                            raw_text=transcription.text,
                            identify_speakers=identify_speakers,
                            correct_grammar=correct_grammar,
                            clean_hesitations=clean_hesitations
                        )
                    else:
                        # Usar processamento tradicional
                        logger.info("Usando pós-processamento tradicional...")
                        corrected_text, processed_segments = PostProcessingService.process_transcription(
                            segments=segments_dict,
                            correct_grammar=correct_grammar,
                            identify_speakers=identify_speakers,
                            clean_hesitations=clean_hesitations
                        )
                    
                    # Formatar conversa
                    formatted_conversation = PostProcessingService.format_conversation(processed_segments)
                    
                    # Atualizar transcrição com resultados processados
                    transcription.text = corrected_text
                    transcription.formatted_conversation = formatted_conversation
                    transcription.post_processed = True
                    
                    # Atualizar segmentos com informações de correção e interlocutor
                    for i, seg in enumerate(transcription.segments):
                        if i < len(processed_segments):
                            proc_seg = processed_segments[i]
                            seg.original_text = proc_seg.original_text
                            seg.text = proc_seg.corrected_text
                            seg.speaker_id = proc_seg.speaker_id
                    
                    logger.info(f"Pós-processamento concluído (LLM: {use_llm})")
                    
                except Exception as e:
                    logger.warning(f"Erro no pós-processamento: {e}. Usando transcrição original.", exc_info=True)
                    # Continuar com transcrição original se houver erro

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
