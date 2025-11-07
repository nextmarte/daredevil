"""
AudioProcessor otimizado usando validação com ffprobe e conversão REMOTA.

✨ DESIGN: Conversão 100% remota em máquina dedicada (192.168.1.33:8591)
   - Validação prévia com ffprobe
   - Conversão remota apenas (sem FFmpeg local)
   - Retry automático com backoff exponencial
   - Detecta arquivo já otimizado (16kHz mono)
"""
import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

# Importar cliente remoto (obrigatório)
try:
    from .remote_audio_converter import RemoteAudioConverter
    REMOTE_CONVERTER_AVAILABLE = True
except ImportError:
    logger.error("❌ CRÍTICO: RemoteAudioConverter não disponível!")
    logger.error("Instale e configure o cliente remoto corretamente.")
    REMOTE_CONVERTER_AVAILABLE = False


class AudioProcessor:
    """Processa e converte arquivos de áudio para formato compatível com Whisper"""

    TEMP_DIR = Path(settings.TEMP_AUDIO_DIR)
    TARGET_SAMPLE_RATE = 16000
    TARGET_CHANNELS = 1
    TARGET_FORMAT = "pcm_s16le"

    @staticmethod
    def ensure_temp_dir():
        """Cria diretório temporário se não existir."""
        AudioProcessor.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, Optional[Dict]]:
        """
        ✅ OTIMIZADO: Valida integridade do arquivo de áudio com ffprobe.
        Detecta rapidamente arquivos corrompidos.

        Returns:
            Tuple[bool, Optional[Dict]]: (is_valid, metadata)
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_format",
                    "-show_streams",
                    "-of", "json",
                    file_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.warning(
                    f"ffprobe falhou para {file_path}: {result.stderr}")
                return False, None

            metadata = json.loads(result.stdout)

            # Validar se tem streams de áudio
            streams = metadata.get("streams", [])
            audio_streams = [s for s in streams if s.get(
                "codec_type") == "audio"]

            if not audio_streams:
                logger.warning(
                    f"Nenhuma faixa de áudio encontrada em {file_path}")
                return False, metadata

            return True, metadata

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout na validação de {file_path}")
            return False, None
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear ffprobe JSON para {file_path}: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Erro ao validar {file_path}: {e}")
            return False, None

    @staticmethod
    def get_audio_info(file_path: str) -> Optional[Dict]:
        """
        ✅ OTIMIZADO: Extrai informações de áudio usando ffprobe.
        Retorna duração, sample rate, canais e codec.
        """
        is_valid, metadata = AudioProcessor.validate_audio_file(file_path)

        if not is_valid or not metadata:
            return None

        try:
            streams = metadata.get("streams", [])
            audio_stream = next(
                (s for s in streams if s.get("codec_type") == "audio"),
                None
            )

            if not audio_stream:
                return None

            duration = float(metadata.get("format", {}).get("duration", 0))
            sample_rate = int(audio_stream.get("sample_rate", 0))
            channels = int(audio_stream.get("channels", 0))
            codec = audio_stream.get("codec_name", "unknown")
            format_name = metadata.get("format", {}).get(
                "format_name", "unknown")

            return {
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "codec": codec,
                "format": format_name,
                "file_size_mb": os.path.getsize(file_path) / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"Erro ao extrair info de áudio: {e}")
            return None

    @staticmethod
    def needs_conversion(audio_info: Optional[Dict]) -> bool:
        """
        ✅ OTIMIZADO: Detecta se arquivo já está em formato otimizado (16kHz, mono).
        Se sim, evita conversão desnecessária (skip de conversão).

        Args:
            audio_info: Dict com informações do áudio

        Returns:
            bool: True se precisa conversão, False se já está otimizado
        """
        if not audio_info:
            return True

        sample_rate = audio_info.get("sample_rate", 0)
        channels = audio_info.get("channels", 0)

        # Se já está 16kHz mono, não precisa converter
        if sample_rate == AudioProcessor.TARGET_SAMPLE_RATE and channels == 1:
            logger.info(
                "✓ Áudio já está otimizado (16kHz mono) - pulando conversão"
            )
            return False

        logger.info(
            f"Arquivo precisa conversão: {sample_rate}Hz {channels}ch -> "
            f"{AudioProcessor.TARGET_SAMPLE_RATE}Hz mono"
        )
        return True

    @staticmethod
    def convert_to_wav(input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        ✅ OTIMIZADO: Converte áudio para WAV 16kHz mono PCM.
        
        ✨ DESIGN: Usa APENAS conversão REMOTA (máquina dedicada)
        
        Fluxo:
        1. Se arquivo já otimizado (16kHz mono) → pula conversão
        2. Sempre tenta conversão REMOTA (192.168.1.29:8591)
        3. Retry automático 2x com backoff exponencial
        4. Se todos os retries falharem → retorna None (erro)

        Por que REMOTA apenas?
        - Máquina com melhor CPU: 5-10x mais rápido
        - Converte TODOS os formatos (FFmpeg disponível)
        - Não sobrecarrega servidor principal
        - Garantia de performance consistente

        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saída (gerado automaticamente se None)

        Returns:
            str: Caminho do arquivo convertido, ou None em erro
            
        Raises:
            None - retorna None em caso de erro (não lança exceção)
        """
        AudioProcessor.ensure_temp_dir()

        # ✅ OTIMIZADO: Validar arquivo antes de converter
        is_valid, audio_info = AudioProcessor.validate_audio_file(input_path)
        if not is_valid:
            logger.error(f"❌ Arquivo de áudio inválido: {input_path}")
            return None

        # ✅ OTIMIZADO: Verificar se precisa conversão
        if not AudioProcessor.needs_conversion(audio_info):
            logger.info(
                f"✓ Arquivo já otimizado (16kHz mono) - pulando conversão: {input_path}")
            return input_path

        # Definir caminho de saída
        if output_path is None:
            output_path = str(
                AudioProcessor.TEMP_DIR / f"audio_{os.urandom(8).hex()}.wav"
            )

        # ✨ OBRIGATÓRIO: Usar conversão REMOTA apenas
        if not REMOTE_CONVERTER_AVAILABLE:
            logger.error(
                "❌ RemoteAudioConverter não importado! Instale/configure corretamente."
            )
            return None

        if not RemoteAudioConverter.ENABLED:
            logger.error(
                "❌ Conversor remoto desabilitado (REMOTE_CONVERTER_ENABLED=false)"
            )
            return None

        logger.info(
            f"🌐 Iniciando conversão REMOTA em 192.168.1.29:8591..."
        )
        
        # Tentar conversão remota (com retry automático internamente)
        remote_result = RemoteAudioConverter.convert_to_wav(
            input_path=input_path,
            output_path=output_path,
            sample_rate=AudioProcessor.TARGET_SAMPLE_RATE,
            channels=AudioProcessor.TARGET_CHANNELS
        )
        
        if remote_result:
            logger.info(f"✓ Conversão remota concluída: {remote_result}")
            return remote_result
        else:
            logger.error(
                f"❌ Falha na conversão remota após {RemoteAudioConverter.MAX_RETRIES} "
                f"retries. Verifique: "
                f"1) Máquina remota ligada (192.168.1.33) "
                f"2) API em 192.168.1.33:8591 "
                f"3) FFmpeg instalado na máquina remota"
            )
            return None

    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Remove arquivo temporário de forma segura."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Arquivo temporário removido: {file_path}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário: {e}")

    @staticmethod
    def extract_audio_from_video(video_path: str, output_path: str) -> str:
        """
        Extrai áudio de arquivo de vídeo (mantém compatibilidade com VideoProcessor).

        Args:
            video_path: Caminho do arquivo de vídeo
            output_path: Caminho do arquivo de áudio de saída

        Returns:
            str: Caminho do arquivo de áudio extraído
        """
        from .video_processor import VideoProcessor

        try:
            logger.info(f"Extraindo áudio de vídeo: {video_path}")

            # ✅ Usar VideoProcessor para extração (já otimizado)
            success, msg = VideoProcessor.extract_audio(
                video_path, output_path)

            if not success:
                raise ValueError(f"Falha na extração de áudio: {msg}")

            logger.info(f"✓ Áudio extraído: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao extrair áudio do vídeo: {e}")
            raise ValueError(f"Falha na extração de áudio: {str(e)}")
