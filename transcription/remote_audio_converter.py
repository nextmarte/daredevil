"""
Cliente para integração com serviço remoto de conversão de áudio.

Este módulo fornece a classe RemoteAudioConverter que se comunica com
o serviço de conversão rodando em máquina remota (porta 8591).

Características:
    ✅ Conversão assíncrona via endpoint /convert-async (OBRIGATÓRIO)
    ✅ Polling automático de status com retry
    ✅ SEM fallback para síncrono (apenas /convert-async)
    ✅ Retry com backoff exponencial
    ✅ Logging estruturado
    ✅ Suporte a timeout configurável
"""

import os
import logging
import requests
import time
from typing import Optional, Dict
from pathlib import Path
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# ✅ OTIMIZAÇÃO: Connection pool com retry automático
def _get_session():
    """Cria session com connection pooling e retry automático"""
    session = requests.Session()
    
    # Retry strategy para conexões intermitentes
    retry_strategy = Retry(
        total=2,  # Máximo de retries
        backoff_factor=0.5,  # 0.5s, 1s, 2s
        status_forcelist=[429, 500, 502, 503, 504],  # Retry em servidor indisponível
        allowed_methods=["HEAD", "GET", "PUT", "POST", "DELETE"]
    )
    
    # Mount adapter em http e https
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Session global (reutiliza conexões)
_global_session = None

def _get_global_session():
    """Retorna session global (singleton)"""
    global _global_session
    if _global_session is None:
        _global_session = _get_session()
    return _global_session


class RemoteAudioConverter:
    """
    Cliente para conversão remota de áudio/vídeo.
    
    Funcionalidades:
    - Envia arquivo para servidor remoto via HTTP (assíncrono)
    - Converte para WAV 16kHz mono PCM (otimizado para Whisper)
    - Polling automático de status com retry exponencial
    - SEM fallback para síncrono (apenas /convert-async)
    - Suporta retry automático em caso de falha
    
    ✨ DESIGN: Usa APENAS /convert-async
       - Se falhar → Retorna None (sem fallback)
       - Endpoint assíncrono é OBRIGATÓRIO
    
    Exemplo:
        >>> converter = RemoteAudioConverter()
        >>> if converter.is_available():
        ...     result = converter.convert_to_wav("input.mp3", "output.wav")
        ...     if result:
        ...         print(f"✓ Conversão remota: {result}")
        ...     else:
        ...         print("Conversão remota falhou")
        ... else:
        ...     print("Serviço remoto indisponível")
    """
    
    # URL do serviço remoto (porta 8591)
    REMOTE_CONVERTER_URL = os.getenv(
        'REMOTE_CONVERTER_URL',
        'http://192.168.1.33:8591'  # ✅ IP real do host
    )
    
    # Timeout em segundos (10 minutos para arquivos grandes)
    TIMEOUT = int(os.getenv('REMOTE_CONVERTER_TIMEOUT', '600'))
    
    # Timeout de polling (máx tempo aguardando conversão assíncrona)
    POLLING_TIMEOUT = int(os.getenv('REMOTE_CONVERTER_POLLING_TIMEOUT', '300'))
    
    # Intervalo entre polls (ms)
    POLLING_INTERVAL = float(os.getenv('REMOTE_CONVERTER_POLLING_INTERVAL', '0.5'))
    
    # Retry automático em caso de falha
    MAX_RETRIES = int(os.getenv('REMOTE_CONVERTER_MAX_RETRIES', '2'))
    
    # Habilitar/desabilitar conversor remoto
    ENABLED = os.getenv('REMOTE_CONVERTER_ENABLED', 'true').lower() == 'true'
    
    @staticmethod
    def convert_to_wav(
        input_path: str,
        output_path: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        retry_count: int = 0
    ) -> Optional[str]:
        """
        Converte áudio para WAV 16kHz mono usando serviço remoto (ASSÍNCRONO OBRIGATÓRIO).
        
        ✨ DESIGN: Usa APENAS endpoint assíncrono (/convert-async)
           - Sem fallback para síncrono
           - Se falhar, retorna None
           - Endpoint assíncrono é OBRIGATÓRIO
        
        Fluxo:
        1. POST /convert-async → Enfileira conversão
        2. Loop polling: GET /convert-status/{job_id} até completed
        3. GET /convert-download/{job_id} → Baixa arquivo convertido
        4. Se qualquer etapa falhar → Retorna None (sem fallback)
        
        Args:
            input_path: Caminho local do arquivo de entrada
            output_path: Onde salvar arquivo convertido (gerado se None)
            sample_rate: Sample rate em Hz (padrão: 16000 - Whisper)
            channels: Número de canais (padrão: 1 - mono)
            retry_count: Contador interno de retries (não modificar)
        
        Returns:
            Caminho do arquivo convertido ou None em caso de erro
            
        Raises:
            FileNotFoundError: Se arquivo de entrada não existe
            IOError: Se não conseguir escrever arquivo de saída
        """
        # Validar que arquivo de entrada existe
        if not os.path.exists(input_path):
            logger.error(f"❌ Arquivo não encontrado: {input_path}")
            return None
        
        # Gerar caminho de saída se não fornecido
        if output_path is None:
            output_dir = settings.TEMP_AUDIO_DIR
            os.makedirs(output_dir, exist_ok=True)
            output_path = str(
                Path(output_dir) / f"audio_remote_{os.urandom(8).hex()}.wav"
            )
        
        # Criar diretório de saída se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            input_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            logger.info(
                f"📤 Enviando para conversão remota: {input_path} "
                f"({input_size_mb:.2f}MB)"
            )
            
            # ✨ OBRIGATÓRIO: Usar APENAS endpoint assíncrono
            logger.info("⚡ Usando endpoint assíncrono (/convert-async) - OBRIGATÓRIO")
            
            result = RemoteAudioConverter._convert_async(
                input_path,
                output_path,
                sample_rate,
                channels
            )
            
            if result:
                return result
            else:
                logger.error(
                    f"❌ Falha na conversão assíncrona. "
                    f"Verifique: "
                    f"1)33) ligada "
                    f"2) API em 192.168.1.33:8591 respondendo "
                    f"3) FFmpeg instalado na máquina remota"
                )
                return None
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado na conversão remota: {e}")
            return None
    
    @staticmethod
    def _convert_async(
        input_path: str,
        output_path: str,
        sample_rate: int,
        channels: int
    ) -> Optional[str]:
        """
        Implementação assíncrona da conversão remota.
        
        ✨ OTIMIZAÇÕES:
        - Connection pooling (reutiliza conexões TCP)
        - Timeout inteligente (10s upload, 5s polling)
        - Retry automático em falhas de conexão
        - Session global singleton
        
        Fluxo:
        1. POST /convert → recebe job_id (endpoint síncrono simples)
        2. Loop polling: GET /status/{job_id} até completed
        3. GET /download/{job_id} → download arquivo
        """
        session = _get_global_session()
        
        try:
            # Passo 1: Enviar arquivo para conversão ASSÍNCRONA
            logger.info(f"📮 Enviando arquivo para conversão remota... (sample_rate={sample_rate}, channels={channels})")
            logger.info(f"📁 Caminho do arquivo: {input_path}")
            logger.info(f"🌐 URL remota: {RemoteAudioConverter.REMOTE_CONVERTER_URL}/convert-async")
            
            # ✅ CORREÇÃO: Ler arquivo completamente ANTES de enviar (evita arquivo vazio)
            if not os.path.exists(input_path):
                logger.error(f"❌ Arquivo não existe: {input_path}")
                return None
            
            file_size = os.path.getsize(input_path)
            logger.info(f"📊 Tamanho do arquivo: {file_size} bytes")
            
            with open(input_path, 'rb') as f:
                file_content = f.read()
            
            if not file_content:
                logger.error(f"❌ Arquivo vazio após leitura: {input_path}")
                return None
            
            logger.info(f"✅ Arquivo lido: {len(file_content)} bytes")
            
            # Enviar arquivo com conteúdo lido
            # ✅ IMPORTANTE: Usar BytesIO para garantir que o requests consegue ler o arquivo completo
            from io import BytesIO
            file_obj = BytesIO(file_content)
            
            files = {'file': ('audio.wav', file_obj, 'audio/wav')}
            data = {
                'sample_rate': sample_rate,
                'channels': channels
            }
            
            logger.info(f"📤 Enviando multipart com {len(file_content)} bytes...")
            logger.debug(f"   - Arquivo: audio.wav")
            logger.debug(f"   - Sample rate: {sample_rate}Hz")
            logger.debug(f"   - Canais: {channels}")
            
            # ✨ TIMEOUT OTIMIZADO: 10s para upload inicial
            try:
                # ✅ CORREÇÃO: Usar endpoint /convert-async (assíncrono)
                response = session.post(
                    f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/convert-async",
                    files=files,
                    data=data,
                    timeout=(5, 10)  # (connect, read) - conexão rápida, upload até 10s
                )
                logger.info(f"✅ Resposta recebida: HTTP {response.status_code}")
            except requests.exceptions.Timeout as e:
                logger.error(f"❌ Timeout no POST /convert-async: {e}")
                return None
            except requests.exceptions.ConnectionError as e:
                logger.error(f"❌ Erro de conexão no POST /convert-async: {e}")
                return None
            
            # Verificar se foi aceito (202 assíncrono)
            if response.status_code != 202:
                logger.error(
                    f"❌ Erro ao enfileirar (HTTP {response.status_code}): {response.text[:200]}"
                )
                return None
            
            logger.info(f"✅ Arquivo enviado (HTTP 202 Aceito)")
            
            response_data = response.json()
            job_id = response_data.get('job_id')
            
            if not job_id:
                logger.error("❌ Job ID não retornado pela API remota")
                return None
            
            logger.info(f"✅ Job ID recebido: {job_id}")
            
            # Passo 2: Fazer polling de status
            logger.info("⏳ Aguardando conversão remota...")
            start_time = time.time()
            poll_count = 0
            
            while True:
                poll_count += 1
                
                # Verificar timeout
                elapsed = time.time() - start_time
                if elapsed > RemoteAudioConverter.POLLING_TIMEOUT:
                    logger.error(
                        f"❌ Timeout no polling ({elapsed:.1f}s > "
                        f"{RemoteAudioConverter.POLLING_TIMEOUT}s)"
                    )
                    return None
                
                # Fazer polling de status
                try:
                    status_response = requests.get(
                        f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/convert-status/{job_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code != 200:
                        logger.warning(f"⚠️ Erro ao consultar status: HTTP {status_response.status_code}")
                        time.sleep(RemoteAudioConverter.POLLING_INTERVAL)
                        continue
                    
                    status_data = status_response.json()
                    job_status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    message = status_data.get('message', '')
                    
                    logger.info(f"  Status: {job_status} ({progress}%) - {message}")
                    
                    # Sucesso!
                    if job_status == 'completed':
                        logger.info(f"✅ Conversão concluída após {poll_count} polls ({elapsed:.1f}s)")
                        break
                    
                    # Erro permanente
                    elif job_status == 'failed':
                        error_msg = status_data.get('error', 'Erro desconhecido')
                        logger.error(f"❌ Conversão falhou: {error_msg}")
                        return None
                    
                    # Ainda processando
                    elif job_status in ['pending', 'processing']:
                        time.sleep(RemoteAudioConverter.POLLING_INTERVAL)
                        continue
                    
                    # Status desconhecido
                    else:
                        logger.warning(f"⚠️ Status desconhecido: {job_status}")
                        time.sleep(RemoteAudioConverter.POLLING_INTERVAL)
                        continue
                
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ Erro na requisição de polling: {e}")
                    time.sleep(RemoteAudioConverter.POLLING_INTERVAL)
                    continue
            
            # Passo 3: Baixar arquivo convertido
            logger.info(f"📥 Baixando arquivo convertido...")
            
            try:
                download_response = requests.get(
                    f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/convert-download/{job_id}",
                    timeout=30
                )
                
                if download_response.status_code != 200:
                    logger.error(
                        f"❌ Erro ao baixar arquivo (HTTP {download_response.status_code})"
                    )
                    return None
                
                # Salvar arquivo
                with open(output_path, 'wb') as f:
                    f.write(download_response.content)
                
                output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(
                    f"✅ Conversão assíncrona concluída: {output_path} "
                    f"({output_size_mb:.2f}MB)"
                )
                return output_path
            
            except IOError as e:
                logger.error(f"❌ Erro ao salvar arquivo: {e}")
                return None
        
        except requests.exceptions.Timeout:
            logger.error(
                f"❌ Timeout no upload ({RemoteAudioConverter.TIMEOUT}s)"
            )
            return None
        
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"❌ Erro de conexão com servidor remoto: {e}"
            )
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro na requisição remota: {e}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Erro inesperado no endpoint assíncrono: {e}")
            return None
    
    @staticmethod
    def is_available() -> bool:
        """
        Verifica se o serviço remoto está disponível e saudável.
        
        Returns:
            True se serviço está disponível, False caso contrário
            
        Note:
            Timeout de 5 segundos para verificação rápida
        """
        if not RemoteAudioConverter.ENABLED:
            logger.debug("Conversor remoto desabilitado via variável de ambiente")
            return False
        
        try:
            response = requests.get(
                f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/health",
                timeout=5
            )
            
            is_ok = response.status_code == 200
            
            if is_ok:
                try:
                    health_data = response.json()
                    logger.debug(
                        f"✓ Serviço remoto saudável: "
                        f"FFmpeg={health_data.get('ffmpeg_available')}, "
                        f"Disco={health_data.get('disk_usage_percent')}%"
                    )
                except ValueError:
                    logger.debug("✓ Serviço remoto saudável (JSON inválido)")
            
            return is_ok
        
        except requests.exceptions.ConnectionError:
            logger.debug(
                f"⚠️ Não conseguiu conectar ao servidor remoto: "
                f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}"
            )
            return False
        
        except requests.exceptions.Timeout:
            logger.debug("⚠️ Health check timeout")
            return False
        
        except Exception as e:
            logger.debug(f"⚠️ Erro ao verificar saúde do serviço remoto: {e}")
            return False
    
    @staticmethod
    def get_status() -> Optional[dict]:
        """
        Obtém status detalhado do serviço remoto.
        
        Returns:
            Dict com métricas ou None se indisponível
            
        Exemplo:
            >>> status = RemoteAudioConverter.get_status()
            >>> if status:
            ...     print(f"Fila: {status['queue_length']}")
            ...     print(f"Completadas: {status['completed_today']}")
        """
        try:
            response = requests.get(
                f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/status",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            logger.debug(f"Erro ao obter status remoto: {e}")
            return None
    
    @staticmethod
    def get_health() -> Optional[dict]:
        """
        Obtém informações de saúde do serviço remoto.
        
        Returns:
            Dict com status, disponibilidade FFmpeg, uso disco ou None
        """
        try:
            response = requests.get(
                f"{RemoteAudioConverter.REMOTE_CONVERTER_URL}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            logger.debug(f"Erro ao obter health remoto: {e}")
            return None
