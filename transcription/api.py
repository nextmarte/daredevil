"""
API endpoints usando Django Ninja
"""
import os
import time
import logging
from typing import List, Optional
from pathlib import Path
import shutil

from ninja import NinjaAPI, File, Form
from ninja.files import UploadedFile
from django.conf import settings
from django.http import HttpRequest

from .schemas import (
    TranscriptionResponse,
    HealthResponse,
    BatchTranscriptionResponse,
    TranscribeRequest
)
from .services import TranscriptionService, WhisperTranscriber

logger = logging.getLogger(__name__)

# Criar instância da API
api = NinjaAPI(
    title="Daredevil Transcription API",
    version="1.0.0",
    description="API de transcrição de áudio em português usando Whisper"
)


@api.get("/health", response=HealthResponse, tags=["Health"])
def health_check(request: HttpRequest):
    """
    Verifica o status da API e configurações

    Retorna informações sobre o modelo carregado e configurações disponíveis.
    """
    try:
        # Tentar carregar modelo para verificar se está OK
        model_name = settings.WHISPER_MODEL
        WhisperTranscriber.load_model(model_name)
        status = "healthy"
    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        status = "unhealthy"

    ffmpeg_available = shutil.which('ffmpeg') is not None
    ffprobe_available = shutil.which('ffprobe') is not None

    return HealthResponse(
        status=status,
        whisper_model=settings.WHISPER_MODEL,
        supported_formats=settings.SUPPORTED_AUDIO_FORMATS,
        max_file_size_mb=settings.MAX_AUDIO_SIZE_MB,
        temp_dir=settings.TEMP_AUDIO_DIR,
        dependencies={
            "ffmpeg": ffmpeg_available,
            "ffprobe": ffprobe_available,
        },
    model_loaded=WhisperTranscriber._model is not None,
        version="1.0.0"
    )


@api.post("/transcribe", response=TranscriptionResponse, tags=["Transcription"])
def transcribe_audio(
    request: HttpRequest,
    file: UploadedFile = File(...),
    language: str = Form("pt")
):
    """
    Transcreve um arquivo de áudio

    ### Parâmetros:
    - **file**: Arquivo de áudio (formatos suportados: opus, ogg, m4a, aac, mp4, mp3, wav, flac, webm)
    - **language**: Código do idioma (padrão: pt)
    - **model**: Modelo Whisper a usar (tiny, base, small, medium, large) - opcional

    ### Retorna:
    - Transcrição completa com timestamps
    - Informações sobre o áudio processado
    - Tempo de processamento

    ### Exemplos de uso:
    - Áudio do WhatsApp: .opus, .ogg
    - Áudio do Instagram: .mp4, .m4a
    - Áudio padrão: .mp3, .wav
    """
    start_time = time.time()
    temp_file_path = None

    # Extrair model do form data se presente
    model = request.POST.get('model', None)

    try:
        # Validar tamanho do arquivo
        file_size_mb = len(file.read()) / (1024 * 1024)
        file.seek(0)  # Resetar ponteiro

        if file_size_mb > settings.MAX_AUDIO_SIZE_MB:
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {settings.MAX_AUDIO_SIZE_MB}MB)"
            )

        # Validar extensão
        file_extension = Path(file.name).suffix.lstrip('.').lower()
        if file_extension not in settings.SUPPORTED_AUDIO_FORMATS:
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=f"Formato '{file_extension}' não suportado. Formatos aceitos: {', '.join(settings.SUPPORTED_AUDIO_FORMATS)}"
            )

        # Salvar arquivo temporário
        temp_file_path = os.path.join(
            settings.TEMP_AUDIO_DIR,
            f"upload_{int(time.time())}_{os.getpid()}.{file_extension}"
        )

        with open(temp_file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        logger.info(f"Arquivo salvo: {temp_file_path} ({file_size_mb:.2f}MB)")

        # Processar áudio
        result = TranscriptionService.process_audio_file(
            file_path=temp_file_path,
            language=language,
            model=model
        )

        return result

    except Exception as e:
        logger.error(f"Erro no endpoint /transcribe: {e}", exc_info=True)
        return TranscriptionResponse(
            success=False,
            transcription=None,
            processing_time=time.time() - start_time,
            audio_info=None,
            error=f"Erro interno: {str(e)}"
        )

    finally:
        # Limpar arquivo temporário
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Arquivo temporário removido: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo: {e}")


@api.post("/transcribe/batch", response=BatchTranscriptionResponse, tags=["Transcription"])
def transcribe_batch(
    request: HttpRequest,
    files: List[UploadedFile] = File(...),
    language: str = Form("pt")
):
    """
    Transcreve múltiplos arquivos de áudio em lote

    ### Parâmetros:
    - **files**: Lista de arquivos de áudio
    - **language**: Código do idioma (padrão: pt)
    - **model**: Modelo Whisper a usar - opcional

    ### Retorna:
    - Lista de resultados para cada arquivo
    - Estatísticas do processamento em lote
    - Tempo total de processamento

    ### Nota:
    Os arquivos são processados sequencialmente. Para grandes volumes,
    considere usar um sistema de filas (Celery, RQ, etc).
    """
    start_time = time.time()
    results = []
    successful = 0
    failed = 0

    # Extrair model do form data se presente
    model = request.POST.get('model', None)

    logger.info(f"Processamento em lote iniciado: {len(files)} arquivos")

    for idx, file in enumerate(files, 1):
        logger.info(f"Processando arquivo {idx}/{len(files)}: {file.name}")

        temp_file_path = None
        try:
            # Salvar arquivo temporário
            file_extension = Path(file.name).suffix.lstrip('.').lower()
            temp_file_path = os.path.join(
                settings.TEMP_AUDIO_DIR,
                f"batch_{int(time.time())}_{idx}.{file_extension}"
            )

            with open(temp_file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            # Processar
            result = TranscriptionService.process_audio_file(
                file_path=temp_file_path,
                language=language,
                model=model
            )

            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file.name}: {e}")
            results.append(TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=0,
                audio_info=None,
                error=str(e)
            ))
            failed += 1

        finally:
            # Limpar arquivo temporário
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo: {e}")

    total_time = time.time() - start_time
    logger.info(
        f"Processamento em lote concluído: {successful} sucesso, {failed} falhas em {total_time:.2f}s")

    return BatchTranscriptionResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results,
        total_processing_time=round(total_time, 2)
    )


# Endpoint adicional para listar formatos suportados
@api.get("/formats", tags=["Info"])
def list_supported_formats(request: HttpRequest):
    """
    Lista todos os formatos de áudio suportados

    Retorna informações sobre os formatos aceitos pela API,
    incluindo formatos específicos do WhatsApp e Instagram.
    """
    return {
        "supported_formats": settings.SUPPORTED_AUDIO_FORMATS,
        "max_file_size_mb": settings.MAX_AUDIO_SIZE_MB,
        "whatsapp_formats": ["opus", "ogg", "m4a", "aac"],
        "instagram_formats": ["mp4", "m4a", "aac"],
        "standard_formats": ["mp3", "wav", "flac", "webm"]
    }
