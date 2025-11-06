"""
Celery tasks for asynchronous transcription processing
"""
import os
import logging
import time
from typing import Optional
from celery import shared_task
from django.conf import settings

from .services import TranscriptionService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='transcription.transcribe_audio_async',
    time_limit=1800,  # 30 minutos (hard limit)
    soft_time_limit=1700,  # 28 minutos (aviso antes do hard limit)
    max_retries=2,
    default_retry_delay=60,  # 1 minuto entre retries
    # ✅ CRITICAL FIX: Adicionar configurações para evitar deadlock
    acks_late=True,  # Reconhece tarefa apenas após conclusão (permite retry se worker morrer)
    reject_on_worker_lost=True,  # Rejeita tarefa se worker morrer
    # Retry apenas em erros recuperáveis (não em todos)
    autoretry_for=(ConnectionError, TimeoutError, IOError),  # Apenas erros de I/O/rede
    retry_backoff=True,  # Backoff exponencial entre retries
    retry_backoff_max=600,  # Máximo de 10 minutos entre retries
    retry_jitter=True  # Adiciona jitter aleatório para evitar thundering herd
)
def transcribe_audio_async(
    self,
    file_path: str,
    language: Optional[str] = None,
    model: Optional[str] = None,
    webhook_url: Optional[str] = None,
    use_cache: bool = True
):
    """
    Tarefa assíncrona para transcrever áudio/vídeo
    
    Args:
        file_path: Caminho do arquivo no servidor
        language: Idioma da transcrição
        model: Modelo Whisper a usar
        webhook_url: URL para notificar quando concluído (opcional)
        use_cache: Se deve usar cache
        
    Returns:
        Dict com resultado da transcrição
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Iniciando transcrição assíncrona: {file_path}")
    
    start_time = time.time()
    
    try:
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"[Task {task_id}] Arquivo não encontrado: {file_path}")
            return {
                "success": False,
                "error": "Arquivo não encontrado",
                "task_id": task_id
            }
        
        # Processar transcrição
        result = TranscriptionService.process_audio_file(
            file_path=file_path,
            language=language,
            model=model,
            use_cache=use_cache
        )
        
        processing_time = time.time() - start_time
        logger.info(f"[Task {task_id}] Transcrição concluída em {processing_time:.2f}s")
        
        # Converter resultado para dict
        result_dict = result.dict()
        result_dict["task_id"] = task_id
        result_dict["total_time"] = round(processing_time, 2)
        
        # Enviar webhook se fornecido
        if webhook_url and result.success:
            try:
                _send_webhook_notification(webhook_url, result_dict)
            except Exception as e:
                logger.error(f"[Task {task_id}] Erro ao enviar webhook: {e}")
        
        return result_dict
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Erro na transcrição: {e}", exc_info=True)
        
        # Tentar retry se não foi timeout
        if "timeout" not in str(e).lower() and self.request.retries < self.max_retries:
            logger.info(f"[Task {task_id}] Tentando novamente em 60 segundos...")
            raise self.retry(exc=e)
        
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id,
            "processing_time": round(time.time() - start_time, 2)
        }
    
    finally:
        # Limpar arquivo temporário se existir
        if file_path and os.path.exists(file_path):
            try:
                # Apenas remover se for arquivo temporário
                if "upload_" in file_path or "temp_" in file_path:
                    os.remove(file_path)
                    logger.info(f"[Task {task_id}] Arquivo temporário removido: {file_path}")
            except Exception as e:
                logger.warning(f"[Task {task_id}] Erro ao remover arquivo: {e}")


@shared_task(
    bind=True,
    name='transcription.transcribe_batch_async',
    time_limit=3600,  # 1 hora para batch (hard limit)
    soft_time_limit=3400,  # 56 minutos (aviso)
    # ✅ CRITICAL FIX: Adicionar configurações para evitar deadlock
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=1,  # Menos retries para batch jobs
    autoretry_for=(ConnectionError, TimeoutError, IOError),  # Apenas erros de I/O/rede
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def transcribe_batch_async(
    self,
    file_paths: list,
    language: Optional[str] = None,
    model: Optional[str] = None,
    webhook_url: Optional[str] = None
):
    """
    Tarefa assíncrona para transcrever múltiplos arquivos em lote
    
    Args:
        file_paths: Lista de caminhos de arquivos
        language: Idioma da transcrição
        model: Modelo Whisper a usar
        webhook_url: URL para notificar quando concluído
        
    Returns:
        Dict com resultados de todas as transcrições
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Iniciando batch de {len(file_paths)} arquivos")
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0
    
    for idx, file_path in enumerate(file_paths, 1):
        logger.info(f"[Task {task_id}] Processando arquivo {idx}/{len(file_paths)}")
        
        try:
            result = TranscriptionService.process_audio_file(
                file_path=file_path,
                language=language,
                model=model
            )
            
            results.append(result.dict())
            
            if result.success:
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"[Task {task_id}] Erro no arquivo {file_path}: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "file_path": file_path
            })
            failed += 1
    
    total_time = time.time() - start_time
    
    batch_result = {
        "task_id": task_id,
        "total_files": len(file_paths),
        "successful": successful,
        "failed": failed,
        "results": results,
        "total_processing_time": round(total_time, 2)
    }
    
    # Enviar webhook se fornecido
    if webhook_url:
        try:
            _send_webhook_notification(webhook_url, batch_result)
        except Exception as e:
            logger.error(f"[Task {task_id}] Erro ao enviar webhook: {e}")
    
    logger.info(
        f"[Task {task_id}] Batch concluído: {successful} sucesso, "
        f"{failed} falhas em {total_time:.2f}s"
    )
    
    return batch_result


def _send_webhook_notification(webhook_url: str, data: dict) -> None:
    """
    Envia notificação webhook com resultado da transcrição
    
    Args:
        webhook_url: URL do webhook
        data: Dados a enviar
    """
    import requests
    
    try:
        response = requests.post(
            webhook_url,
            json=data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        logger.info(f"Webhook enviado com sucesso para {webhook_url}")
    except Exception as e:
        logger.error(f"Erro ao enviar webhook para {webhook_url}: {e}")
        raise
