"""
Sistema de cache inteligente para transcrições
Implementa cache baseado em hash com política LRU e TTL configurável
"""
import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from collections import OrderedDict
from threading import Lock
from django.conf import settings

logger = logging.getLogger(__name__)


class LRUCache:
    """Cache LRU thread-safe com TTL configurável"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Args:
            max_size: Número máximo de itens no cache
            ttl_seconds: Tempo de vida dos itens em segundos (padrão: 1 hora)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = Lock()
        self._hits = 0
        self._misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém item do cache se existir e não expirou
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor cacheado ou None se não existir/expirado
        """
        with self.lock:
            if key not in self.cache:
                self._misses += 1
                return None
            
            # Verificar TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                logger.debug(f"Cache expirado para chave: {key[:16]}...")
                self._remove(key)
                self._misses += 1
                return None
            
            # Mover para o final (mais recente)
            self.cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Cache HIT para chave: {key[:16]}...")
            return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        Adiciona ou atualiza item no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser cacheado
        """
        with self.lock:
            # Se já existe, remover para atualizar posição
            if key in self.cache:
                self._remove(key)
            
            # Adicionar novo item
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            # Remover item mais antigo se exceder tamanho máximo
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                logger.debug(f"Cache cheio, removendo item mais antigo: {oldest_key[:16]}...")
                self._remove(oldest_key)
            
            logger.debug(f"Cache SET para chave: {key[:16]}...")
    
    def _remove(self, key: str) -> None:
        """Remove item do cache (internal use)"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Cache limpo completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        with self.lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "ttl_seconds": self.ttl_seconds
            }


class TranscriptionCacheManager:
    """Gerenciador de cache para transcrições com persistência opcional"""
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        memory_cache_size: int = 100,
        ttl_seconds: int = 3600,
        enable_disk_cache: bool = False
    ):
        """
        Args:
            cache_dir: Diretório para cache em disco (opcional)
            memory_cache_size: Tamanho do cache em memória
            ttl_seconds: TTL para itens do cache
            enable_disk_cache: Se True, persiste cache em disco
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(settings.TEMP_AUDIO_DIR) / "cache"
        self.enable_disk_cache = enable_disk_cache
        self.memory_cache = LRUCache(max_size=memory_cache_size, ttl_seconds=ttl_seconds)
        
        if self.enable_disk_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache em disco habilitado: {self.cache_dir}")
    
    def generate_cache_key(self, file_path: str, model: str = None, language: str = None) -> str:
        """
        Gera chave única de cache baseada no conteúdo do arquivo e parâmetros
        
        Args:
            file_path: Caminho do arquivo
            model: Modelo Whisper usado
            language: Idioma da transcrição
            
        Returns:
            Hash MD5 como chave do cache
        """
        # Hash do conteúdo do arquivo
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Incluir modelo e idioma na chave
        cache_key_data = f"{file_hash}_{model or settings.WHISPER_MODEL}_{language or settings.WHISPER_LANGUAGE}"
        cache_key = hashlib.md5(cache_key_data.encode()).hexdigest()
        
        return cache_key
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Busca transcrição no cache (memória primeiro, depois disco)
        
        Args:
            cache_key: Chave do cache
            
        Returns:
            Dados da transcrição cacheada ou None
        """
        # Tentar cache em memória primeiro
        cached_data = self.memory_cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Se habilitado, tentar cache em disco
        if self.enable_disk_cache:
            return self._load_from_disk(cache_key)
        
        return None
    
    def set(self, cache_key: str, transcription_data: Dict[str, Any]) -> None:
        """
        Armazena transcrição no cache
        
        Args:
            cache_key: Chave do cache
            transcription_data: Dados da transcrição a cachear
        """
        # Adicionar timestamp ao dado
        transcription_data["cached_at"] = time.time()
        
        # Salvar em memória
        self.memory_cache.set(cache_key, transcription_data)
        
        # Salvar em disco se habilitado
        if self.enable_disk_cache:
            self._save_to_disk(cache_key, transcription_data)
    
    def _save_to_disk(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Salva dados no cache em disco"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cache salvo em disco: {cache_key[:16]}...")
        except Exception as e:
            logger.error(f"Erro ao salvar cache em disco: {e}")
    
    def _load_from_disk(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Carrega dados do cache em disco"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if not cache_file.exists():
                return None
            
            # Verificar idade do arquivo
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age > self.memory_cache.ttl_seconds:
                logger.debug(f"Cache em disco expirado: {cache_key[:16]}...")
                cache_file.unlink()  # Remover arquivo expirado
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Carregar de volta na memória para acesso rápido
            self.memory_cache.set(cache_key, data)
            logger.debug(f"Cache carregado do disco: {cache_key[:16]}...")
            return data
            
        except Exception as e:
            logger.error(f"Erro ao carregar cache do disco: {e}")
            return None
    
    def clear(self) -> None:
        """Limpa todo o cache (memória e disco)"""
        self.memory_cache.clear()
        
        if self.enable_disk_cache:
            try:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.info("Cache em disco limpo")
            except Exception as e:
                logger.error(f"Erro ao limpar cache em disco: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas completas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        stats = self.memory_cache.get_stats()
        
        if self.enable_disk_cache:
            try:
                disk_files = list(self.cache_dir.glob("*.json"))
                stats["disk_cache_size"] = len(disk_files)
                stats["disk_cache_enabled"] = True
            except Exception:
                stats["disk_cache_size"] = 0
                stats["disk_cache_enabled"] = False
        else:
            stats["disk_cache_enabled"] = False
            stats["disk_cache_size"] = 0
        
        return stats


# Instância global do gerenciador de cache
_cache_manager: Optional[TranscriptionCacheManager] = None


def get_cache_manager() -> TranscriptionCacheManager:
    """
    Retorna instância singleton do gerenciador de cache
    
    Returns:
        TranscriptionCacheManager singleton
    """
    global _cache_manager
    
    if _cache_manager is None:
        # Configurar cache baseado em variáveis de ambiente
        cache_size = int(os.getenv('CACHE_SIZE', 100))
        cache_ttl = int(os.getenv('CACHE_TTL_SECONDS', 3600))  # 1 hora padrão
        enable_disk = os.getenv('ENABLE_DISK_CACHE', 'false').lower() == 'true'
        
        _cache_manager = TranscriptionCacheManager(
            memory_cache_size=cache_size,
            ttl_seconds=cache_ttl,
            enable_disk_cache=enable_disk
        )
        
        logger.info(
            f"Cache manager inicializado: size={cache_size}, "
            f"ttl={cache_ttl}s, disk={enable_disk}"
        )
    
    return _cache_manager
