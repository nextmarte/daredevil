"""
Celery tasks for asynchronous transcription processing
"""
import os
import logging
import time
from typing import Optional
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings

from .services import TranscriptionService, WhisperTranscriber
from .memory_manager import MemoryManager  # ✅ NOVO: Proteção de memória

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='transcription.transcribe_audio_async',
    queue='gpu',  # ✅ NOVO: Rotear para GPU worker
    time_limit=1800,  # 30 minutos
    soft_time_limit=1700,  # 28 minutos (aviso)
    max_retries=3,  # Aumentado de 2 para 3
    default_retry_delay=60,  # 1 minuto entre retries
    autoretry_for=(ConnectionError, OSError),  # Auto-retry em erros de conexão Redis
    retry_backoff=True,  # Backoff exponencial
    retry_backoff_max=600,  # Máximo de 10 minutos
    retry_jitter=True  # Adicionar jitter para evitar thundering herd
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
    
    file_removed = False  # Flag para rastrear se arquivo foi removido
    
    try:
        # Verificar se arquivo existe
        if not os.path.exists(file_path):
            logger.error(f"[Task {task_id}] Arquivo não encontrado: {file_path}")
            return {
                "success": False,
                "error": "Arquivo não encontrado",
                "task_id": task_id
            }
        
        logger.debug(f"[Task {task_id}] Arquivo confirmado: {file_path} ({os.path.getsize(file_path)} bytes)")
        
        # Processar transcrição
        # Garantir que language seja string
        lang = language if language else "pt"
        result = TranscriptionService.process_audio_file(
            file_path=file_path,
            language=lang,
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
        
    except SoftTimeLimitExceeded:
        # Timeout iminente - limpar e abortar graciosamente
        logger.warning(f"[Task {task_id}] Soft time limit atingido, abortando...")
        return {
            "success": False,
            "error": "Tempo limite de processamento atingido (soft timeout)",
            "task_id": task_id,
            "processing_time": round(time.time() - start_time, 2)
        }
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Erro na transcrição: {e}", exc_info=True)
        
        # Tentar retry se não foi timeout e arquivo ainda existe
        if "timeout" not in str(e).lower() and self.request.retries < self.max_retries:
            if os.path.exists(file_path):
                logger.info(f"[Task {task_id}] Tentando novamente em 60 segundos...")
                raise self.retry(exc=e)
            else:
                logger.error(f"[Task {task_id}] Arquivo foi removido, não pode fazer retry!")
                return {
                    "success": False,
                    "error": f"Arquivo foi removido antes do retry: {file_path}",
                    "task_id": task_id,
                    "processing_time": round(time.time() - start_time, 2)
                }
        
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id,
            "processing_time": round(time.time() - start_time, 2)
        }
    
    finally:
        # Limpar memória GPU para evitar vazamento
        try:
            WhisperTranscriber.clear_gpu_memory()
        except Exception as e:
            logger.warning(f"[Task {task_id}] Erro ao limpar GPU: {e}")
        
        # ✅ CORREÇÃO: Remover arquivo temporário APENAS APÓS processamento bem-sucedido
        # Manter arquivo por um tempo se houve erro (para possíveis debugs/retries)
        if file_path and os.path.exists(file_path) and not file_removed:
            try:
                # Apenas remover se for arquivo de upload assíncrono
                if "upload_async_" in file_path or "upload_" in file_path or "temp_" in file_path:
                    os.remove(file_path)
                    file_removed = True
                    logger.info(f"[Task {task_id}] Arquivo temporário removido: {file_path}")
                else:
                    logger.debug(f"[Task {task_id}] Arquivo não será removido (não é temporário): {file_path}")
            except Exception as e:
                logger.warning(f"[Task {task_id}] Erro ao remover arquivo: {e}")


@shared_task(
    bind=True,
    name='transcription.transcribe_batch_async',
    time_limit=3600,  # 1 hora para batch
    soft_time_limit=3400,
    max_retries=2,
    default_retry_delay=120,  # 2 minutos entre retries para batch
    autoretry_for=(ConnectionError, OSError),  # Auto-retry em erros de conexão Redis
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
    
    try:
        for idx, file_path in enumerate(file_paths, 1):
            logger.info(f"[Task {task_id}] Processando arquivo {idx}/{len(file_paths)}")
            
            try:
                # Garantir que language seja string
                lang = language if language else "pt"
                result = TranscriptionService.process_audio_file(
                    file_path=file_path,
                    language=lang,
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
    
    except SoftTimeLimitExceeded:
        # Timeout iminente - retornar resultados parciais
        logger.warning(f"[Task {task_id}] Soft time limit atingido em batch, retornando resultados parciais")
        batch_result = {
            "task_id": task_id,
            "total_files": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results,
            "total_processing_time": round(time.time() - start_time, 2),
            "partial": True,
            "error": "Timeout atingido, resultados parciais"
        }
        return batch_result
    
    total_time = time.time() - start_time
    
    batch_result = {
        "task_id": task_id,
        "total_files": len(file_paths),
        "successful": successful,
        "failed": failed,
        "results": results,
        "total_processing_time": round(total_time, 2)
    }
    
    try:
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
    finally:
        # Limpar memória GPU após batch
        try:
            WhisperTranscriber.clear_gpu_memory()
        except Exception as e:
            logger.warning(f"[Task {task_id}] Erro ao limpar GPU: {e}")



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


# ========== TASKS DE PROTEÇÃO CONTRA TRAVAMENTO ==========
# ✅ NOVAS TASKS: Limpeza automática de recursos


@shared_task(
    name='transcription.cleanup_temp_files_task',
    bind=True,
    time_limit=600,  # 10 minutos
)
def cleanup_temp_files_task(self):
    """
    ✅ PROTEÇÃO: Task agendada para limpar arquivos temporários antigos
    
    Executa a cada 30 minutos (configurável em Celery Beat).
    Remove arquivos com idade > 6 horas para liberar espaço em disco.
    
    ⚠️ IMPORTANTE: Aumentado de 1h para 6h para evitar deletar arquivos
    que ainda estão sendo processados por tasks assíncronas na fila.
    
    Retorna:
        Dict com número de arquivos removidos e status
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] Iniciando limpeza de arquivos temporários...")
    
    try:
        # Remover arquivos com idade > 6 horas (aumentado de 1h)
        deleted = MemoryManager.cleanup_old_temp_files(max_age_hours=6)
        
        # Forçar limpeza agressiva se disco > 85%
        MemoryManager.force_cleanup_if_needed()
        
        # Obter status de memória
        usage = MemoryManager.get_memory_usage()
        
        result = {
            "success": True,
            "deleted_files": deleted,
            "disk_usage_percent": usage.get("disk_percent", 0),
            "ram_usage_percent": usage.get("ram_percent", 0),
            "temp_dir_size_mb": MemoryManager.get_temp_dir_size_mb(),
        }
        
        logger.info(f"[Task {task_id}] Limpeza concluída: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Erro ao limpar temporários: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task(
    name='transcription.monitor_memory_task',
    bind=True,
    time_limit=300,  # 5 minutos
)
def monitor_memory_task(self):
    """
    ✅ PROTEÇÃO: Task agendada para monitorar uso de memória
    
    Executa a cada 5 minutos (configurável em Celery Beat).
    Alerta se memória/disco atingir níveis críticos.
    
    Retorna:
        Dict com status de memória
    """
    task_id = self.request.id
    
    try:
        usage = MemoryManager.get_memory_usage()
        status = MemoryManager.get_status()
        
        # Log conforme o nível
        if status["is_critical"]:
            logger.critical(f"🔴 [Task {task_id}] ALERTA CRÍTICO DE MEMÓRIA: {usage}")
        elif status["is_warning"]:
            logger.warning(f"⚠️  [Task {task_id}] AVISO DE MEMÓRIA: {usage}")
        else:
            logger.debug(f"[Task {task_id}] Status normal: RAM={usage.get('ram_percent', 0)}% Disco={usage.get('disk_percent', 0)}%")
        
        return {
            "success": True,
            "is_critical": status["is_critical"],
            "is_warning": status["is_warning"],
            "memory_usage": usage
        }
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Erro ao monitorar memória: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@shared_task(
    name='transcription.unload_gpu_model_task',
    bind=True,
    time_limit=60,  # 1 minuto
)
def unload_gpu_model_task(self):
    """
    ✅ PROTEÇÃO: Task agendada para descarregar modelo de GPU periodicamente
    
    Executa a cada 1 hora (configurável em Celery Beat).
    Descarrega modelo de GPU se não estiver em uso para liberar memória.
    
    Retorna:
        Dict com status
    """
    task_id = self.request.id
    
    try:
        # Descarregar modelo se estiver em GPU
        WhisperTranscriber.unload_model()
        
        logger.info(f"[Task {task_id}] Modelo de GPU descarregado com sucesso")
        
        return {
            "success": True,
            "message": "Modelo de GPU descarregado"
        }
        
    except Exception as e:
        logger.error(f"[Task {task_id}] Erro ao descarregar modelo: {e}")
        return {
            "success": False,
            "error": str(e)
        }

