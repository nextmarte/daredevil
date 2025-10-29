"""
Processador de vídeos para extração de áudio
Converte vários formatos de vídeo para áudio WAV otimizado para transcrição
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Processa vídeos e extrai áudio para transcrição"""

    # Formatos de vídeo suportados
    SUPPORTED_VIDEO_FORMATS = [
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'ogv',
        'ts', 'mts', 'm2ts', '3gp', 'f4v', 'asf'
    ]

    @staticmethod
    def validate_video_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Valida arquivo de vídeo

        Args:
            file_path: Caminho do arquivo de vídeo

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "Arquivo não encontrado"

        extension = Path(file_path).suffix.lstrip('.').lower()
        if extension not in VideoProcessor.SUPPORTED_VIDEO_FORMATS:
            return False, f"Formato de vídeo '{extension}' não suportado"

        # Verificar se ffmpeg consegue ler o arquivo
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=codec_type', '-of', 'csv=p=0',
                 file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, "Arquivo de vídeo corrompido ou inválido"
            
            return True, None
        except FileNotFoundError:
            return False, "ffprobe não encontrado. Instale ffmpeg."
        except subprocess.TimeoutExpired:
            return False, "Timeout ao validar arquivo de vídeo"
        except Exception as e:
            return False, f"Erro ao validar vídeo: {str(e)}"

    @staticmethod
    def get_video_info(file_path: str) -> dict:
        """
        Extrai informações do arquivo de vídeo usando ffprobe

        Args:
            file_path: Caminho do arquivo de vídeo

        Returns:
            dict: Informações do vídeo (duração, resolução, codecs, etc.)
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                 '-print_json', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                info = {
                    'duration': 0,
                    'has_audio': False,
                    'has_video': False,
                    'video_codec': None,
                    'audio_codec': None,
                    'resolution': None
                }
                
                # Extrair duração
                if 'format' in data and 'duration' in data['format']:
                    info['duration'] = float(data['format']['duration'])
                
                # Extrair informações de streams
                for stream in data.get('streams', []):
                    if stream['codec_type'] == 'video':
                        info['has_video'] = True
                        info['video_codec'] = stream.get('codec_name')
                        if 'width' in stream and 'height' in stream:
                            info['resolution'] = f"{stream['width']}x{stream['height']}"
                    elif stream['codec_type'] == 'audio':
                        info['has_audio'] = True
                        info['audio_codec'] = stream.get('codec_name')
                
                logger.info(f"Informações do vídeo: {info}")
                return info
        except Exception as e:
            logger.warning(f"Erro ao extrair informações do vídeo: {e}")
            return {}

    @staticmethod
    def extract_audio(video_path: str, output_path: str, timeout: int = 600) -> Tuple[bool, str]:
        """
        Extrai áudio de arquivo de vídeo usando ffmpeg

        Args:
            video_path: Caminho do arquivo de vídeo
            output_path: Caminho de saída para o arquivo WAV
            timeout: Tempo máximo de execução em segundos (padrão 10 minutos)

        Returns:
            Tuple[bool, str]: (sucesso, mensagem_ou_caminho)
        """
        try:
            logger.info(f"Extraindo áudio de vídeo: {video_path}")
            
            # Comando ffmpeg para extrair áudio
            # -i: arquivo de entrada
            # -vn: sem vídeo
            # -acodec pcm_s16le: codec de áudio PCM 16-bit
            # -ar 16000: taxa de amostragem 16kHz (otimizado para Whisper)
            # -ac 1: mono (1 canal)
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',                      # Sem vídeo
                '-acodec', 'pcm_s16le',     # Codec de áudio
                '-ar', '16000',             # Taxa de amostragem
                '-ac', '1',                 # Mono
                '-loglevel', 'error',       # Apenas erros
                '-y',                       # Sobrescrever arquivo
                output_path
            ]
            
            logger.debug(f"Executando: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Áudio extraído com sucesso: {output_path} ({file_size_mb:.2f}MB)")
                return True, output_path
            else:
                error_msg = result.stderr or "Erro desconhecido ao extrair áudio"
                logger.error(f"Erro ao extrair áudio: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao processar vídeo (limite: {timeout}s)")
            return False, f"Timeout ao processar vídeo (limite: {timeout}s)"
        except FileNotFoundError:
            logger.error("ffmpeg não encontrado. Instale ffmpeg no sistema.")
            return False, "ffmpeg não encontrado. Instale ffmpeg."
        except Exception as e:
            logger.error(f"Erro ao extrair áudio: {e}")
            return False, str(e)

    @staticmethod
    def extract_audio_with_compression(
        video_path: str,
        output_path: str,
        bitrate: str = '128k',
        timeout: int = 600
    ) -> Tuple[bool, str]:
        """
        Extrai áudio com compressão (MP3/AAC) para reduzir tamanho

        Args:
            video_path: Caminho do arquivo de vídeo
            output_path: Caminho de saída para o arquivo comprimido
            bitrate: Taxa de bits (ex: 128k, 192k, 256k)
            timeout: Tempo máximo de execução em segundos

        Returns:
            Tuple[bool, str]: (sucesso, mensagem_ou_caminho)
        """
        try:
            logger.info(f"Extraindo áudio comprimido de vídeo: {video_path}")
            
            # Determinar formato de saída pela extensão
            ext = Path(output_path).suffix.lstrip('.').lower()
            
            if ext == 'mp3':
                codec = 'libmp3lame'
            elif ext in ('aac', 'm4a'):
                codec = 'aac'
            else:
                ext = 'mp3'
                codec = 'libmp3lame'
                output_path = output_path.replace(Path(output_path).suffix, '.mp3')
            
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', codec,
                '-ab', bitrate,
                '-ar', '16000',
                '-ac', '1',
                '-loglevel', 'error',
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"Áudio comprimido: {output_path} ({file_size_mb:.2f}MB)")
                return True, output_path
            else:
                error_msg = result.stderr or "Erro ao extrair áudio comprimido"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Erro ao extrair áudio comprimido: {e}")
            return False, str(e)

    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """Verifica se o arquivo é um vídeo"""
        extension = Path(file_path).suffix.lstrip('.').lower()
        return extension in VideoProcessor.SUPPORTED_VIDEO_FORMATS


class MediaTypeDetector:
    """Detecta tipo de mídia (áudio, vídeo)"""

    @staticmethod
    def detect_media_type(file_path: str) -> str:
        """
        Detecta se arquivo é áudio ou vídeo

        Returns:
            str: 'audio', 'video', ou 'unknown'
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', file_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                has_video = any(s['codec_type'] == 'video' for s in data.get('streams', []))
                has_audio = any(s['codec_type'] == 'audio' for s in data.get('streams', []))
                
                if has_video and has_audio:
                    return 'video'
                elif has_audio:
                    return 'audio'
                elif has_video:
                    return 'video'
            
            return 'unknown'
        except Exception as e:
            logger.warning(f"Erro ao detectar tipo de mídia: {e}")
            return 'unknown'
