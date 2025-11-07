"""
API endpoints usando Django Ninja
"""
import os
import time
import logging
from typing import List, Optional
from pathlib import Path

import torch
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
from .cache_manager import get_cache_manager
from .memory_manager import MemoryManager  # ✅ NOVO: Proteção de memória

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

    return HealthResponse(
        status=status,
        whisper_model=settings.WHISPER_MODEL,
        supported_formats=settings.ALL_SUPPORTED_FORMATS,
        max_file_size_mb=settings.MAX_AUDIO_SIZE_MB,
        temp_dir=settings.TEMP_AUDIO_DIR
    )


@api.get("/gpu-status", tags=["Health"])
def gpu_status(request: HttpRequest):
    """
    Verifica o status da GPU e uso de memória
    
    Retorna informações sobre GPUs disponíveis e uso atual de memória.
    """
    device = WhisperTranscriber.get_device()
    
    if device == "cpu":
        return {
            "gpu_available": False,
            "device": "cpu",
            "message": "Nenhuma GPU disponível. Usando CPU para processamento."
        }
    
    gpu_info = {
        "gpu_available": True,
        "device": device,
        "gpu_count": torch.cuda.device_count(),
        "gpus": []
    }
    
    for i in range(torch.cuda.device_count()):
        memory_allocated = torch.cuda.memory_allocated(i) / (1024**3)
        memory_reserved = torch.cuda.memory_reserved(i) / (1024**3)
        memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
        
        gpu_info["gpus"].append({
            "id": i,
            "name": torch.cuda.get_device_name(i),
            "memory_allocated_gb": round(memory_allocated, 2),
            "memory_reserved_gb": round(memory_reserved, 2),
            "memory_total_gb": round(memory_total, 2),
            "memory_free_gb": round(memory_total - memory_reserved, 2),
            "compute_capability": f"{torch.cuda.get_device_capability(i)[0]}.{torch.cuda.get_device_capability(i)[1]}"
        })
    
    return gpu_info


@api.get("/memory-status", tags=["Health"])
def memory_status(request: HttpRequest):
    """
    Retorna o status de memória e disco do servidor
    
    ✅ PROTEÇÃO: Permite monitorar recursos e detectar travamentos potenciais.
    
    Retorna informações sobre:
    - RAM (percentual de uso, disponível, total)
    - Disco (percentual de uso, livre, total)
    - Tamanho de arquivos temporários
    - Status crítico/aviso
    """
    return MemoryManager.get_status()


@api.post("/cleanup-temp", tags=["Health"])
def cleanup_temp_files(request: HttpRequest):
    """
    Limpa arquivos temporários antigos
    
    ✅ PROTEÇÃO: Remove arquivos com mais de 1 hora para liberar espaço em disco.
    
    Retorna número de arquivos removidos e espaço liberado.
    """
    try:
        deleted = MemoryManager.cleanup_old_temp_files(max_age_hours=1)
        usage = MemoryManager.get_memory_usage()
        return {
            "success": True,
            "deleted_files": deleted,
            "message": f"{deleted} arquivos temporários removidos",
            "disk_usage_percent": usage.get("disk_percent", 0)
        }
    except Exception as e:
        logger.error(f"Erro ao limpar temporários: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@api.get("/cache-stats", tags=["Health"])
def cache_stats(request: HttpRequest):
    """
    Retorna estatísticas do cache de transcrições
    
    Mostra hits, misses, hit rate e tamanho atual do cache.
    """
    if not settings.ENABLE_CACHE:
        return {
            "cache_enabled": False,
            "message": "Cache desabilitado"
        }
    
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        stats["cache_enabled"] = True
        return stats
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        return {
            "cache_enabled": True,
            "error": str(e)
        }


@api.post("/cache/clear", tags=["Health"])
def clear_cache(request: HttpRequest):
    """
    Limpa todo o cache de transcrições
    
    Remove todos os itens do cache em memória e disco (se habilitado).
    Requer autenticação em produção.
    """
    if not settings.ENABLE_CACHE:
        return {
            "success": False,
            "message": "Cache desabilitado"
        }
    
    try:
        cache_manager = get_cache_manager()
        cache_manager.clear()
        return {
            "success": True,
            "message": "Cache limpo com sucesso"
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@api.post("/transcribe", response=TranscriptionResponse, tags=["Transcription"])
def transcribe_audio(
    request: HttpRequest,
    file: UploadedFile = File(...),
    language: str = Form("pt")
):
    """
    Transcreve um arquivo de áudio ou vídeo

    ### Parâmetros:
    - **file**: Arquivo de áudio ou vídeo (ver formatos suportados abaixo)
    - **language**: Código do idioma (padrão: **pt** para português brasileiro)
    - **model**: Modelo Whisper a usar (tiny, base, small, medium, large) - opcional

    ### Formatos de Áudio Suportados:
    **WhatsApp**: .opus, .ogg  
    **Instagram/Redes Sociais**: .mp4, .m4a, .aac  
    **Padrão**: .mp3, .wav, .flac, .webm  

    ### Formatos de Vídeo Suportados:
    .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm, .ogv, .ts, .mts, .m2ts, .3gp, .f4v, .asf  
    **Nota**: O áudio será automaticamente extraído em qualidade otimizada para transcrição.

    ### Linguagens Suportadas:
    - **pt**: Português Brasileiro (padrão) ⭐
    - en: Inglês
    - es: Espanhol
    - fr: Francês
    - de: Alemão
    - it: Italiano
    - E outros idiomas suportados pelo Whisper

    ### Retorna:
    - Transcrição completa com timestamps
    - Informações sobre o áudio/vídeo processado
    - Tempo total de processamento

    ### Otimizações para Português:
    - Remove hesitações comuns (tipo, sabe, entendeu, né, etc.)
    - Capitalização correta de frases
    - Pontuação normalizada
    - Abreviações expandidas

    ### Limite de Tamanho:
    Máximo 500MB por arquivo

    ### Exemplos de uso:
    - Áudio do WhatsApp: .opus, .ogg
    - Vídeo do Instagram: .mp4 (áudio extraído automaticamente)
    - Áudio padrão: .mp3, .wav
    - Vídeo local: .mkv, .mov, .avi
    """
    start_time = time.time()
    temp_file_path = None

    # Extrair model do form data se presente
    model = request.POST.get('model', None)

    try:
        # ✅ PROTEÇÃO 1: Verificar se memória está crítica
        if MemoryManager.check_memory_critical():
            logger.warning("🔴 Requisição rejeitada: Servidor com memória/disco crítico")
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error="Servidor com memória/disco crítico. Tente novamente mais tarde."
            )
        
        # Validar tamanho do arquivo ANTES de carregar na memória
        # Usar file.size em vez de file.read() para evitar OutOfMemory
        file_size_mb = file.size / (1024 * 1024)

        # ✅ PROTEÇÃO 2: Verificar se deve rejeitar upload por espaço/memória
        should_reject, reject_reason = MemoryManager.should_reject_upload(file_size_mb)
        if should_reject:
            logger.warning(f"⚠️  Upload rejeitado: {reject_reason}")
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=reject_reason or "Não há recursos disponíveis. Tente novamente mais tarde."
            )

        if file_size_mb > settings.MAX_AUDIO_SIZE_MB:
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {settings.MAX_AUDIO_SIZE_MB}MB)"
            )

        # Validar extensão (áudio OU vídeo)
        file_extension = Path(file.name).suffix.lstrip('.').lower()
        supported_formats = settings.ALL_SUPPORTED_FORMATS
        
        if file_extension not in supported_formats:
            return TranscriptionResponse(
                success=False,
                transcription=None,
                processing_time=time.time() - start_time,
                audio_info=None,
                error=f"Formato '{file_extension}' não suportado. Formatos aceitos: {', '.join(sorted(supported_formats))}"
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

        # Processar áudio (language padrão é português)
        result = TranscriptionService.process_audio_file(
            file_path=temp_file_path,
            language=language if language != "pt" else None,  # None usa o padrão
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
            # Validar tamanho ANTES de carregar na memória
            file_size_mb = file.size / (1024 * 1024)
            if file_size_mb > settings.MAX_AUDIO_SIZE_MB:
                logger.warning(f"Arquivo {file.name} muito grande: {file_size_mb:.2f}MB")
                results.append(TranscriptionResponse(
                    success=False,
                    transcription=None,
                    processing_time=0,
                    audio_info=None,
                    error=f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {settings.MAX_AUDIO_SIZE_MB}MB)"
                ))
                failed += 1
                continue
            
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
@api.get("/formats", tags=["Health"])
def list_supported_formats(request: HttpRequest):
    """
    Lista todos os formatos suportados pela API

    Retorna formatos de áudio e vídeo separados, além do limite máximo de arquivo.
    """
    return {
        "audio_formats": sorted(settings.SUPPORTED_AUDIO_FORMATS),
        "video_formats": sorted(settings.SUPPORTED_VIDEO_FORMATS),
        "all_formats": sorted(settings.ALL_SUPPORTED_FORMATS),
        "max_file_size_mb": settings.MAX_AUDIO_SIZE_MB,
        "notes": {
            "video_conversion": "Arquivos de vídeo serão convertidos para áudio automaticamente",
            "audio_optimization": "Áudio será normalizado para 16kHz, mono",
            "portuguese_default": "Português Brasileiro é o idioma padrão e otimizado"
        }
    }


# Async endpoints
@api.post("/transcribe/async", tags=["Async Transcription"])
def transcribe_audio_async_endpoint(
    request: HttpRequest,
    file: UploadedFile = File(...),
    language: str = Form("pt"),
    webhook_url: Optional[str] = Form(None)
):
    """
    Transcreve arquivo de áudio/vídeo de forma assíncrona (Polling ou Webhook)
    
    ✅ **Suporta 2 modos de notificação:**
    1. **Polling**: Consulte o status via GET `/api/transcribe/async/status/{task_id}`
    2. **Webhook**: Forneça `webhook_url` para receber POST automático quando concluir
    
    ### Parâmetros (form-data):
    
    | Parâmetro | Tipo | Obrigatório | Descrição |
    |-----------|------|------------|-----------|
    | **file** | File | ✅ Sim | Arquivo de áudio ou vídeo (até 500MB) |
    | **language** | String | ❌ Não | Código do idioma (padrão: `pt` para português) |
    | **model** | String | ❌ Não | Modelo Whisper: `tiny`, `base`, `small`, `medium`, `large` |
    | **webhook_url** | String | ❌ Não | URL para receber POST com resultado (opcional) |
    
    ### Formatos de Áudio Suportados:
    .opus, .ogg, .m4a, .aac, .mp4, .mp3, .wav, .flac, .webm
    
    ### Formatos de Vídeo Suportados:
    .mp4, .avi, .mov, .mkv, .flv, .wmv, .webm, .ogv, .ts, .mts, .m2ts, .3gp, .f4v, .asf
    
    ### Retorna (200 OK):
    ```json
    {
      "success": true,
      "task_id": "abc123def456",
      "status_url": "/api/transcribe/async/status/abc123def456",
      "message": "Transcrição iniciada. Use task_id para consultar o status.",
      "submission_time": 0.25
    }
    ```
    
    ### Modo 1: POLLING (sem webhook)
    
    **Passo 1:** Upload do arquivo
    ```bash
    curl -X POST http://localhost:8000/api/transcribe/async \\
      -F "file=@audio.mp3" \\
      -F "language=pt"
    # Retorna: {"task_id": "abc123", "status_url": "/api/transcribe/async/status/abc123"}
    ```
    
    **Passo 2:** Consulte o status periodicamente
    ```bash
    curl http://localhost:8000/api/transcribe/async/status/abc123
    # Retorna: {"state": "STARTED", "message": "Transcrição em andamento"}
    # Retorna: {"state": "SUCCESS", "result": {...}}
    ```
    
    ### Modo 2: WEBHOOK (notificação automática)
    
    **Passo 1:** Upload com webhook_url
    ```bash
    curl -X POST http://localhost:8000/api/transcribe/async \\
      -F "file=@audio.mp3" \\
      -F "language=pt" \\
      -F "webhook_url=https://seu-servidor.com/webhook"
    # Retorna: {"task_id": "abc123", ...}
    ```
    
    **Passo 2:** Sua API receberá POST quando concluir
    ```json
    POST https://seu-servidor.com/webhook
    {
      "task_id": "abc123",
      "success": true,
      "result": {
        "text": "transcrição aqui",
        "segments": [...],
        ...
      }
    }
    ```
    
    ### Estados da Tarefa:
    - **PENDING**: Aguardando na fila de processamento
    - **STARTED**: Processamento iniciado
    - **SUCCESS**: Concluída com sucesso ✅
    - **FAILURE**: Falhou ❌
    - **RETRY**: Tentando novamente após erro
    
    ### Vantagens:
    - ⚡ Não bloqueia a requisição (retorna imediatamente)
    - 🔄 Ideal para arquivos grandes (> 100MB)
    - 🌐 Suporta polling para ambientes com firewall restritivo
    - 📝 Suporta webhook para aplicações real-time
    - 🔁 Retry automático em caso de falha
    - ✅ Processamento em fila (não sobrecarrega servidor)
    """
    from .tasks import transcribe_audio_async
    
    start_time = time.time()
    temp_file_path = None
    
    # Extrair model do form data se presente
    model = request.POST.get('model', None)
    
    try:
        # Validar tamanho ANTES de carregar na memória
        file_size_mb = file.size / (1024 * 1024)
        
        if file_size_mb > settings.MAX_AUDIO_SIZE_MB:
            return {
                "success": False,
                "error": f"Arquivo muito grande: {file_size_mb:.2f}MB (máximo: {settings.MAX_AUDIO_SIZE_MB}MB)"
            }
        
        # Validar extensão
        file_extension = Path(file.name).suffix.lstrip('.').lower()
        if file_extension not in settings.ALL_SUPPORTED_FORMATS:
            return {
                "success": False,
                "error": f"Formato '{file_extension}' não suportado"
            }
        
        # Salvar arquivo temporário
        temp_file_path = os.path.join(
            settings.TEMP_AUDIO_DIR,
            f"upload_async_{int(time.time())}_{os.getpid()}.{file_extension}"
        )
        
        with open(temp_file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        logger.info(f"Arquivo salvo para processamento assíncrono: {temp_file_path}")
        
        # Enviar para fila Celery
        task = transcribe_audio_async.delay(
            file_path=temp_file_path,
            language=language if language != "pt" else None,
            model=model,
            webhook_url=webhook_url
        )
        
        return {
            "success": True,
            "task_id": task.id,
            "status_url": f"/api/transcribe/async/status/{task.id}",
            "message": "Transcrição iniciada. Use task_id para consultar o status.",
            "submission_time": round(time.time() - start_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Erro ao iniciar transcrição assíncrona: {e}")
        # Limpar arquivo se houve erro
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        
        return {
            "success": False,
            "error": str(e)
        }


@api.get("/transcribe/async/status/{task_id}", tags=["Async Transcription"])
def get_async_task_status(request: HttpRequest, task_id: str):
    """
    ✅ Consulta o status de uma tarefa de transcrição assíncrona (POLLING)
    
    **Use este endpoint para polling ao invés de webhook**
    
    ### Parâmetros:
    - **task_id** (path): ID da tarefa retornado pelo endpoint POST `/api/transcribe/async`
    
    ### Retorna (200 OK):
    
    #### Enquanto processando:
    ```json
    {
      "task_id": "abc123def456",
      "state": "STARTED",
      "message": "Transcrição em andamento"
    }
    ```
    
    #### Quando concluído com sucesso:
    ```json
    {
      "task_id": "abc123def456",
      "state": "SUCCESS",
      "result": {
        "success": true,
        "transcription": {
          "text": "texto completo da transcrição",
          "segments": [
            {
              "start": 0.0,
              "end": 2.5,
              "text": "primeira parte"
            }
          ],
          "language": "pt",
          "duration": 45.5
        },
        "audio_info": {
          "format": "mp3",
          "duration": 45.5,
          "sample_rate": 16000
        },
        "processing_time": 12.3
      },
      "message": "Transcrição concluída"
    }
    ```
    
    #### Quando falha:
    ```json
    {
      "task_id": "abc123def456",
      "state": "FAILURE",
      "error": "Motivo do erro",
      "message": "Transcrição falhou"
    }
    ```
    
    ### Estados Possíveis:
    
    | Estado | Descrição | Ação |
    |--------|-----------|------|
    | **PENDING** | Aguardando na fila | Aguarde... |
    | **STARTED** | Processamento iniciado | Aguarde... |
    | **SUCCESS** | ✅ Concluído com sucesso | Use `result` |
    | **FAILURE** | ❌ Falhou | Verifique `error` |
    | **RETRY** | Tentando novamente | Aguarde... |
    
    ### Exemplo de Polling:
    
    ```python
    import requests
    import time
    
    # 1. Fazer upload
    response = requests.post(
        'http://localhost:8000/api/transcribe/async',
        files={'file': open('audio.mp3', 'rb')},
        data={'language': 'pt'}
    )
    task_id = response.json()['task_id']
    print(f"Task iniciada: {task_id}")
    
    # 2. Polling até concluir
    while True:
        status = requests.get(
            f'http://localhost:8000/api/transcribe/async/status/{task_id}'
        ).json()
        
        print(f"Estado: {status['state']}")
        
        if status['state'] == 'SUCCESS':
            print(f"Transcrição: {status['result']['transcription']['text']}")
            break
        elif status['state'] == 'FAILURE':
            print(f"Erro: {status['error']}")
            break
        else:
            time.sleep(2)  # Aguardar 2 segundos antes de perguntar novamente
    ```
    
    ### Estratégias de Polling:
    
    **1. Polling Simples (a cada 2 segundos)**
    ```bash
    while true; do
      curl http://localhost:8000/api/transcribe/async/status/abc123
      sleep 2
    done
    ```
    
    **2. Polling Exponencial (aumenta intervalo com tempo)**
    ```bash
    for i in 1 2 3 4 5; do
      curl http://localhost:8000/api/transcribe/async/status/abc123
      sleep $((i * 2))  # 2s, 4s, 6s, 8s, 10s
    done
    ```
    
    **3. Polling com Limite (máximo 10 min)**
    ```bash
    start=$(date +%s)
    timeout=600
    while true; do
      elapsed=$(($(date +%s) - start))
      if [ $elapsed -gt $timeout ]; then
        echo "Timeout!"
        break
      fi
      curl http://localhost:8000/api/transcribe/async/status/abc123
      sleep 3
    done
    ```
    
    ### ⚠️ Recomendações:
    - Não consulte mais que **1 vez a cada segundo** (respeite o servidor!)
    - Use intervalo de **2-5 segundos** para melhor balanço
    - Implemente **timeout máximo** (ex: 30 minutos)
    - Para arquivos grandes (> 500MB), use intervalo maior (10-30s)
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "state": task.state,
    }
    
    if task.state == 'PENDING':
        response["message"] = "Tarefa aguardando processamento"
    elif task.state == 'STARTED':
        response["message"] = "Transcrição em andamento"
    elif task.state == 'SUCCESS':
        response["result"] = task.result
        response["message"] = "Transcrição concluída"
    elif task.state == 'FAILURE':
        response["error"] = str(task.info)
        response["message"] = "Transcrição falhou"
    elif task.state == 'RETRY':
        response["message"] = "Tentando novamente após erro"
    else:
        response["message"] = f"Estado: {task.state}"
    
    return response


@api.delete("/transcribe/async/{task_id}", tags=["Async Transcription"])
def cancel_async_task(request: HttpRequest, task_id: str):
    """
    ❌ Cancela uma tarefa de transcrição assíncrona em andamento
    
    ### Parâmetros:
    - **task_id** (path): ID da tarefa a cancelar
    
    ### Retorna (200 OK):
    
    #### Cancelada com sucesso:
    ```json
    {
      "success": true,
      "message": "Tarefa cancelada",
      "task_id": "abc123def456"
    }
    ```
    
    #### Não pode ser cancelada:
    ```json
    {
      "success": false,
      "message": "Tarefa já concluída com estado: SUCCESS",
      "state": "SUCCESS"
    }
    ```
    
    ### Nota Importante:
    ⚠️ **Limitações do cancelamento:**
    - Tarefas **em processamento** podem não ser interrompidas imediatamente
    - Tarefas já **concluídas** não podem ser canceladas
    - Tarefas na **fila** serão canceladas imediatamente
    
    ### Exemplo:
    ```bash
    # Cancelar transcrição
    curl -X DELETE http://localhost:8000/api/transcribe/async/abc123
    
    # Resultado possível:
    # {"success": true, "message": "Tarefa cancelada"}
    ```
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    if task.state in ['SUCCESS', 'FAILURE']:
        return {
            "success": False,
            "message": f"Tarefa já concluída com estado: {task.state}"
        }
    
    try:
        task.revoke(terminate=True)
        return {
            "success": True,
            "message": "Tarefa cancelada",
            "task_id": task_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

