"""
Gerenciador de memória para proteger o sistema contra travamentos
Monitora RAM, GPU e disco, e rejeita requisições quando recursos críticos
"""
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Union
import shutil

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from django.conf import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Gerencia memória RAM, GPU e disco para evitar travamentos"""
    
    # Limites de segurança
    RAM_THRESHOLD_PERCENT = int(os.getenv('MEMORY_CRITICAL_THRESHOLD_PERCENT', 90))
    DISK_THRESHOLD_PERCENT = int(os.getenv('DISK_CRITICAL_THRESHOLD_PERCENT', 90))
    RAM_WARNING_THRESHOLD_PERCENT = int(os.getenv('MEMORY_WARNING_THRESHOLD_PERCENT', 75))
    TEMP_DIR_MAX_SIZE_MB = int(os.getenv('TEMP_DIR_MAX_SIZE_MB', 5000))  # 5GB
    
    @staticmethod
    def is_psutil_available() -> bool:
        """Verifica se psutil está disponível"""
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil não está instalado. Monitoramento de memória desabilitado.")
            return False
        return True
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Union[float, str]]:
        """
        Retorna uso atual de RAM e disco
        
        Returns:
            Dict com informações de memória (ram_percent, ram_available_gb, disk_percent, etc.)
        """
        if not MemoryManager.is_psutil_available():
            return {
                "ram_percent": 0.0,
                "ram_available_gb": 0.0,
                "ram_total_gb": 0.0,
                "disk_percent": 0.0,
                "disk_free_gb": 0.0,
                "error": "psutil não disponível"
            }
        
        try:
            if PSUTIL_AVAILABLE and psutil is not None:
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                return {
                    "ram_percent": float(memory.percent),
                    "ram_available_gb": round(float(memory.available) / (1024**3), 2),
                    "ram_total_gb": round(float(memory.total) / (1024**3), 2),
                    "ram_used_gb": round(float(memory.used) / (1024**3), 2),
                    "disk_percent": float(disk.percent),
                    "disk_free_gb": round(float(disk.free) / (1024**3), 2),
                    "disk_total_gb": round(float(disk.total) / (1024**3), 2),
                    "disk_used_gb": round(float(disk.used) / (1024**3), 2),
                }
            else:
                return {"error": "psutil não disponível"}
        except Exception as e:
            logger.error(f"Erro ao obter uso de memória: {e}")
            return {
                "error": str(e),
                "ram_percent": 0.0,
                "disk_percent": 0.0
            }
    
    @staticmethod
    def check_memory_critical() -> bool:
        """
        Verifica se memória está CRÍTICA (deve rejeitar requisições)
        
        Returns:
            True se memória/disco está crítico, False caso contrário
        """
        usage = MemoryManager.get_memory_usage()
        
        if "error" in usage:
            # Se psutil não disponível, permanecer conservador
            return False
        
        # RAM crítica - cast seguro
        ram_percent = usage.get("ram_percent", 0.0)
        if isinstance(ram_percent, (int, float)) and ram_percent > MemoryManager.RAM_THRESHOLD_PERCENT:
            logger.critical(f"🔴 RAM CRÍTICA: {ram_percent}%")
            return True
        
        # Disco crítico - cast seguro
        disk_percent = usage.get("disk_percent", 0.0)
        if isinstance(disk_percent, (int, float)) and disk_percent > MemoryManager.DISK_THRESHOLD_PERCENT:
            logger.critical(f"🔴 DISCO CRÍTICO: {disk_percent}%")
            return True
        
        return False
    
    @staticmethod
    def check_memory_warning() -> bool:
        """
        Verifica se memória está em AVISO (pode aceitar, mas com cuidado)
        
        Returns:
            True se em nível de aviso, False caso contrário
        """
        usage = MemoryManager.get_memory_usage()
        
        if "error" in usage:
            return False
        
        ram_percent = usage.get("ram_percent", 0.0)
        if isinstance(ram_percent, (int, float)) and ram_percent > MemoryManager.RAM_WARNING_THRESHOLD_PERCENT:
            logger.warning(f"⚠️  RAM em AVISO: {ram_percent}%")
            return True
        
        return False
    
    @staticmethod
    def cleanup_old_temp_files(max_age_hours: int = 24) -> int:
        """
        Remove arquivos temporários antigos
        
        Args:
            max_age_hours: Idade máxima do arquivo em horas (padrão: 24 horas)
            
        Returns:
            Número de arquivos removidos
        """
        temp_dir = Path(settings.TEMP_AUDIO_DIR)
        
        if not temp_dir.exists():
            logger.debug(f"Diretório temporário não existe: {temp_dir}")
            return 0
        
        import time
        now = time.time()
        deleted = 0
        deleted_size_mb = 0
        
        try:
            for file in temp_dir.glob("*"):
                try:
                    age_hours = (now - file.stat().st_mtime) / 3600
                    
                    if age_hours > max_age_hours:
                        file_size_mb = file.stat().st_size / (1024**2)
                        file.unlink()
                        deleted += 1
                        deleted_size_mb += file_size_mb
                        logger.debug(f"Arquivo temporário removido: {file.name} ({file_size_mb:.2f}MB)")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo {file}: {e}")
        except Exception as e:
            logger.error(f"Erro ao limpar temporários: {e}")
        
        if deleted > 0:
            logger.info(f"Limpeza de temporários: {deleted} arquivos removidos ({deleted_size_mb:.2f}MB)")
        
        return deleted
    
    @staticmethod
    def force_cleanup_if_needed():
        """
        Força limpeza agressiva se espaço em disco estiver baixo
        Remove arquivos com idade > 1 hora
        """
        usage = MemoryManager.get_memory_usage()
        
        disk_percent = usage.get("disk_percent", 0.0)
        if isinstance(disk_percent, (int, float)) and disk_percent > 85:
            logger.warning("Disco > 85%, limpando temporários com idade > 1 hora")
            MemoryManager.cleanup_old_temp_files(max_age_hours=1)
        
        if isinstance(disk_percent, (int, float)) and disk_percent > 95:
            logger.critical("Disco > 95%, limpando TODOS os temporários")
            MemoryManager.cleanup_old_temp_files(max_age_hours=0)
    
    @staticmethod
    def get_temp_dir_size_mb() -> float:
        """
        Calcula tamanho total do diretório temporário
        
        Returns:
            Tamanho total em MB
        """
        temp_dir = Path(settings.TEMP_AUDIO_DIR)
        
        if not temp_dir.exists():
            return 0
        
        try:
            total_size = sum(f.stat().st_size for f in temp_dir.rglob("*") if f.is_file())
            return total_size / (1024**2)
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho: {e}")
            return 0
    
    @staticmethod
    def should_reject_upload(file_size_mb: float) -> tuple[bool, Optional[str]]:
        """
        Verifica se deve rejeitar upload por falta de espaço/memória
        
        Args:
            file_size_mb: Tamanho do arquivo em MB
            
        Returns:
            (deve_rejeitar, mensagem_erro)
        """
        # ✅ PROTEÇÃO 1: Verificar se memória está crítica
        if MemoryManager.check_memory_critical():
            return True, "Servidor com memória/disco crítico. Tente novamente mais tarde."
        
        usage = MemoryManager.get_memory_usage()
        
        if "error" in usage:
            # Se não conseguir verificar, ser conservador
            logger.warning("Não consegui verificar memória, rejeitando upload por segurança")
            return True, "Não consegui verificar recursos do servidor. Tente novamente."
        
        # ✅ PROTEÇÃO 2: Se RAM > 80%, rejeitar
        ram_percent = usage.get("ram_percent", 0.0)
        if isinstance(ram_percent, (int, float)) and ram_percent > 80:
            msg = f"RAM em {ram_percent}% - limite atingido. Tente mais tarde."
            logger.warning(f"Upload rejeitado: {msg}")
            return True, msg
        
        # ✅ PROTEÇÃO 3: Se espaço em disco < 2x tamanho do arquivo, rejeitar
        disk_free_gb = usage.get("disk_free_gb", 0.0)
        if isinstance(disk_free_gb, (int, float)):
            disk_free_mb = disk_free_gb * 1024
            if disk_free_mb < file_size_mb * 2:
                msg = f"Espaço em disco insuficiente ({disk_free_mb:.0f}MB disponível, precisa {file_size_mb*2:.0f}MB)"
                logger.warning(f"Upload rejeitado: {msg}")
                return True, msg
        
        # ✅ PROTEÇÃO 4: Se /tmp/daredevil > limite, rejeitar
        temp_size_mb = MemoryManager.get_temp_dir_size_mb()
        if temp_size_mb + file_size_mb > MemoryManager.TEMP_DIR_MAX_SIZE_MB:
            msg = f"Espaço temporário quase cheio ({temp_size_mb:.0f}MB / {MemoryManager.TEMP_DIR_MAX_SIZE_MB}MB)"
            logger.warning(f"Upload rejeitado: {msg}")
            # Tentar limpar
            MemoryManager.cleanup_old_temp_files(max_age_hours=1)
            return True, msg
        
        return False, None
    
    @staticmethod
    def get_status() -> Dict:
        """
        Retorna status completo do sistema
        
        Returns:
            Dict com informações de memória, disco e alertas
        """
        usage = MemoryManager.get_memory_usage()
        temp_size = MemoryManager.get_temp_dir_size_mb()
        
        status = {
            "memory_usage": usage,
            "temp_dir_size_mb": temp_size,
            "temp_dir_max_mb": MemoryManager.TEMP_DIR_MAX_SIZE_MB,
            "is_critical": MemoryManager.check_memory_critical(),
            "is_warning": MemoryManager.check_memory_warning(),
            "thresholds": {
                "ram_critical_percent": MemoryManager.RAM_THRESHOLD_PERCENT,
                "ram_warning_percent": MemoryManager.RAM_WARNING_THRESHOLD_PERCENT,
                "disk_critical_percent": MemoryManager.DISK_THRESHOLD_PERCENT,
            }
        }
        
        return status
