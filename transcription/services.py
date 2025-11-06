"""
Serviço de processamento de áudio e transcrição usando Whisper
"""
import os
import gc
import time
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict
from contextlib import contextmanager

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
from .cache_manager import get_cache_manager

logger = logging.getLogger(__name__)


# ✅ CRITICAL FIX: Context manager para garantir limpeza de arquivos temporários
@contextmanager
def temporary_file(file_path: Optional[str] = None):
    """
    Context manager para garantir limpeza de arquivos temporários
    
    Usage:
        with temporary_file(temp_path) as path:
            # Usar arquivo temporário
            pass
        # Arquivo é automaticamente removido aqui
    """
    try:
        yield file_path
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Arquivo temporário removido: {file_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")



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
    _gpu_memory_threshold = 0.9  # 90% de uso antes de fallback para CPU

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
    def check_gpu_memory(cls) -> Dict[str, float]:
        """
        Verifica uso atual de memória GPU
        
        Returns:
            Dict com informações de memória (allocated, reserved, total, free)
        """
        if not torch.cuda.is_available():
            return {}
        
        try:
            allocated = torch.cuda.memory_allocated(0) / (1024**3)
            reserved = torch.cuda.memory_reserved(0) / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            free = total - reserved
            usage_percent = (reserved / total) * 100
            
            return {
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "free_gb": round(free, 2),
                "usage_percent": round(usage_percent, 2)
            }
        except Exception as e:
            logger.error(f"Erro ao verificar memória GPU: {e}")
            return {}
    
    @classmethod
    def clear_gpu_memory(cls) -> None:
        """Limpa memória GPU não utilizada"""
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                gc.collect()
                logger.debug("Cache GPU limpo")
            except Exception as e:
                logger.error(f"Erro ao limpar cache GPU: {e}")
    
    @classmethod
    def should_use_cpu_fallback(cls) -> bool:
        """
        Verifica se deve usar fallback para CPU devido a pressão de memória
        
        Returns:
            True se deve usar CPU, False se pode usar GPU
        """
        if not torch.cuda.is_available():
            return True
        
        memory_info = cls.check_gpu_memory()
        if not memory_info:
            return False
        
        usage_percent = memory_info.get("usage_percent", 0) / 100
        if usage_percent > cls._gpu_memory_threshold:
            logger.warning(
                f"GPU com {usage_percent*100:.1f}% de uso, "
                f"usando fallback para CPU"
            )
            return True
        
        return False

    @classmethod
    def load_model(cls, model_name: Optional[str] = None, force_cpu: bool = False) -> whisper.Whisper:
        """
        Carrega modelo Whisper (singleton) no dispositivo apropriado
        Com cache persistente em GPU para evitar recarregamento

        Args:
            model_name: Nome do modelo (tiny, base, small, medium, large)
            force_cpu: Forçar uso de CPU mesmo se GPU disponível

        Returns:
            whisper.Whisper: Modelo carregado
        """
        if model_name is None:
            model_name = settings.WHISPER_MODEL

        # Determinar dispositivo
        if force_cpu or cls.should_use_cpu_fallback():
            device = "cpu"
        else:
            device = cls.get_device()

        # Reutilizar modelo se já estiver carregado no mesmo dispositivo
        if cls._model is not None and cls._current_model_name == model_name:
            # Verificar se está no dispositivo correto
            model_device = str(next(cls._model.parameters()).device)
            if device in model_device or (device == "cpu" and "cuda" not in model_device):
                logger.info(f"Reutilizando modelo Whisper em cache: {model_name} ({device})")
                return cls._model
            else:
                logger.info(f"Modelo em dispositivo diferente, recarregando...")
                cls._model = None
                cls.clear_gpu_memory()

        logger.info(f"Carregando modelo Whisper: {model_name} no dispositivo: {device}")
        start_time = time.time()

        try:
            # Limpar memória antes de carregar modelo grande
            if device == "cuda":
                cls.clear_gpu_memory()
                memory_before = cls.check_gpu_memory()
                logger.info(f"Memória GPU antes do carregamento: {memory_before}")
            
            cls._model = whisper.load_model(model_name, device=device)
            cls._current_model_name = model_name

            load_time = time.time() - start_time
            logger.info(f"Modelo carregado em {load_time:.2f}s")
            
            # Log de memória GPU após carregamento
            if device == "cuda":
                memory_after = cls.check_gpu_memory()
                logger.info(f"Memória GPU após carregamento: {memory_after}")
                memory_used = memory_after.get("reserved_gb", 0) - memory_before.get("reserved_gb", 0)
                logger.info(f"Memória GPU usada pelo modelo: {memory_used:.2f}GB")

            return cls._model

        except RuntimeError as e:
            error_str = str(e)
            if "out of memory" in error_str.lower() and device == "cuda":
                logger.error(f"GPU sem memória suficiente, tentando fallback para CPU...")
                cls.clear_gpu_memory()
                # Tentar novamente em CPU
                return cls.load_model(model_name, force_cpu=True)
            else:
                logger.error(f"Erro ao carregar modelo Whisper: {e}")
                raise RuntimeError(f"Falha ao carregar modelo: {str(e)}")
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
        Transcreve arquivo de áudio com otimizações de GPU

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
        device = str(next(model.parameters()).device)

        logger.info(f"Transcrevendo áudio: {audio_path} (idioma: {language}, device: {device})")
        start_time = time.time()
        
        # Log memória antes da transcrição
        if "cuda" in device:
            memory_before = cls.check_gpu_memory()
            logger.debug(f"Memória GPU antes da transcrição: {memory_before}")

        try:
            # Transcrever com Whisper
            use_fp16 = "cuda" in device  # Usar FP16 apenas em GPU
            result = model.transcribe(
                audio_path,
                language=language,
                verbose=False,
                fp16=use_fp16
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
            
            # Criar resultado antes de limpar memória
            result = TranscriptionResult(
                text=full_text,
                segments=segments,
                language=result.get('language', language),
                duration=result.get('duration', 0)
            )
            
            # ✅ CRITICAL FIX: Limpar memória GPU após cada transcrição para evitar OOM
            if "cuda" in device:
                memory_after = cls.check_gpu_memory()
                logger.debug(f"Memória GPU após transcrição: {memory_after}")
                cls.clear_gpu_memory()
                memory_final = cls.check_gpu_memory()
                logger.info(f"Memória GPU após limpeza: {memory_final.get('free_gb', 0):.2f}GB livres")
            
            return result

        except RuntimeError as e:
            error_str = str(e)
            
            # Tratamento de erro de memória GPU
            if "out of memory" in error_str.lower():
                logger.error("GPU sem memória, tentando novamente com CPU...")
                cls.clear_gpu_memory()
                # Recarregar modelo em CPU e tentar novamente
                model = cls.load_model(model_name, force_cpu=True)
                return cls.transcribe(audio_path, language, model_name)
            
            # Erro específico de tensor vazio do Whisper
            if "cannot reshape tensor of 0 elements" in error_str:
                raise RuntimeError(
                    f"Falha na transcrição: Arquivo de áudio inválido ou vazio. "
                    f"O arquivo pode estar corrompido, não conter áudio válido, ou ter duração muito curta."
                )
            
            raise RuntimeError(f"Falha na transcrição: {error_str}")
        
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            error_str = str(e)
            
            # Erro específico de tensor vazio do Whisper
            if "cannot reshape tensor of 0 elements" in error_str:
                raise RuntimeError(
                    f"Falha na transcrição: Arquivo de áudio inválido ou vazio. "
                    f"O arquivo pode estar corrompido, não conter áudio válido, ou ter duração muito curta."
                )
            
            raise RuntimeError(f"Falha na transcrição: {error_str}")


class TranscriptionService:
    """Serviço principal de transcrição - orquestra todo o processo"""

    @staticmethod
    def generate_cache_key(file_path: str, model: str = None, language: str = None) -> str:
        """
        Gera chave de cache baseada no hash do arquivo e parâmetros
        
        Args:
            file_path: Caminho do arquivo
            model: Modelo usado
            language: Idioma usado
            
        Returns:
            Chave de cache
        """
        cache_manager = get_cache_manager()
        return cache_manager.generate_cache_key(file_path, model, language)

    @staticmethod
    def process_audio_file(
        file_path: str,
        language: str = None,
        model: Optional[str] = None,
        use_cache: bool = True
    ) -> TranscriptionResponse:
        """
        Processa arquivo de áudio ou vídeo completo com cache inteligente

        Args:
            file_path: Caminho do arquivo de áudio ou vídeo
            language: Idioma para transcrição (padrão: português brasileiro)
            model: Modelo Whisper a usar
            use_cache: Se True, usa cache quando disponível

        Returns:
            TranscriptionResponse: Resposta completa da transcrição
        """
        # Usar português como padrão
        if language is None:
            language = settings.WHISPER_LANGUAGE
        
        start_time = time.time()
        temp_wav_path = None
        extension = Path(file_path).suffix.lstrip('.').lower()
        
        # Verificar cache se habilitado
        cache_key = None
        if use_cache and settings.ENABLE_CACHE:
            try:
                cache_manager = get_cache_manager()
                cache_key = cache_manager.generate_cache_key(file_path, model, language)
                cached_result = cache_manager.get(cache_key)
                
                if cached_result:
                    logger.info(f"Usando resultado do cache (chave: {cache_key[:16]}...)")
                    processing_time = time.time() - start_time
                    
                    # Converter dados cacheados de volta para objetos
                    transcription_dict = cached_result.get("transcription")
                    audio_info_dict = cached_result.get("audio_info")
                    
                    # Reconstruir objetos
                    if transcription_dict:
                        segments = [
                            TranscriptionSegment(**seg) 
                            for seg in transcription_dict.get("segments", [])
                        ]
                        transcription = TranscriptionResult(
                            text=transcription_dict["text"],
                            segments=segments,
                            language=transcription_dict["language"],
                            duration=transcription_dict["duration"]
                        )
                    else:
                        transcription = None
                    
                    audio_info = AudioInfo(**audio_info_dict) if audio_info_dict else None
                    
                    return TranscriptionResponse(
                        success=cached_result.get("success", True),
                        transcription=transcription,
                        processing_time=round(processing_time, 2),
                        audio_info=audio_info,
                        error=cached_result.get("error"),
                        cached=True
                    )
            except Exception as e:
                logger.warning(f"Erro ao verificar cache: {e}")
                # Continuar sem cache em caso de erro

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

            # Validar que o arquivo WAV tem conteúdo válido antes de transcrever
            wav_file_size = os.path.getsize(transcribe_path)
            if wav_file_size < 1000:  # Mínimo de 1KB
                logger.error(f"Arquivo WAV muito pequeno ({wav_file_size} bytes) - provavelmente vazio ou corrompido")
                return TranscriptionResponse(
                    success=False,
                    transcription=None,
                    processing_time=time.time() - start_time,
                    audio_info=None,
                    error=f"Arquivo de áudio inválido ou vazio ({wav_file_size} bytes). Pode ser que o arquivo não tenha faixa de áudio ou esteja corrompido."
                )

            # Transcrever
            transcription = WhisperTranscriber.transcribe(
                transcribe_path,
                language=language,
                model_name=model
            )

            processing_time = time.time() - start_time
            
            result = TranscriptionResponse(
                success=True,
                transcription=transcription,
                processing_time=round(processing_time, 2),
                audio_info=audio_info,
                error=None
            )
            
            # Salvar no cache se habilitado
            if use_cache and settings.ENABLE_CACHE and cache_key:
                try:
                    cache_manager = get_cache_manager()
                    # Converter para dicionário para serialização
                    cache_data = {
                        "success": result.success,
                        "transcription": transcription.dict() if transcription else None,
                        "audio_info": audio_info.dict() if audio_info else None,
                        "processing_time": result.processing_time,
                        "error": result.error
                    }
                    cache_manager.set(cache_key, cache_data)
                    logger.info(f"Resultado salvo no cache (chave: {cache_key[:16]}...)")
                except Exception as e:
                    logger.warning(f"Erro ao salvar no cache: {e}")
            
            return result

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
            # ✅ CRITICAL FIX: Garantir limpeza de arquivos temporários mesmo em caso de erro
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    logger.info(f"Arquivo temporário removido: {temp_wav_path}")
                except Exception as e:
                    logger.error(f"CRÍTICO: Falha ao remover arquivo temporário {temp_wav_path}: {e}")
                    # Tentar forçar remoção ajustando permissões (owner apenas)
                    try:
                        os.chmod(temp_wav_path, 0o600)  # Owner pode ler/escrever
                        os.remove(temp_wav_path)
                        logger.info(f"Arquivo temporário removido após ajustar permissões")
                    except Exception as e2:
                        logger.error(f"CRÍTICO: Impossível remover arquivo temporário: {e2}")
                        # Em último caso, adicionar à lista para limpeza posterior
                        # (seria necessário implementar um cleanup job separado)
