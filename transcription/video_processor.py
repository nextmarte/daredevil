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
            
            # Verificar se tem faixa de áudio
            if not result.stdout.strip():
                return False, "Arquivo de vídeo não contém faixa de áudio"
            
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
    def calculate_adaptive_timeout(file_path: str, base_timeout: int = 300) -> int:
        """
        Calcula timeout adaptativo baseado no tamanho do arquivo
        
        Args:
            file_path: Caminho do arquivo de vídeo
            base_timeout: Timeout base em segundos (padrão: 5 minutos)
            
        Returns:
            Timeout calculado em segundos
        """
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Timeout adaptativo: 30s por MB, mínimo 5min, máximo 30min
            # Vídeos pequenos (<10MB): 5 minutos
            # Vídeos médios (10-100MB): 5-15 minutos
            # Vídeos grandes (100-500MB): 15-30 minutos
            adaptive_timeout = base_timeout + int(file_size_mb * 30)
            
            # Limitar entre 5 e 30 minutos
            adaptive_timeout = max(300, min(1800, adaptive_timeout))
            
            logger.debug(f"Timeout adaptativo para {file_size_mb:.2f}MB: {adaptive_timeout}s")
            return adaptive_timeout
            
        except Exception as e:
            logger.warning(f"Erro ao calcular timeout adaptativo: {e}, usando padrão")
            return base_timeout

    @staticmethod
    def extract_audio(video_path: str, output_path: str, timeout: int = None) -> Tuple[bool, str]:
        """
        Extrai áudio de arquivo de vídeo usando ffmpeg com timeout adaptativo
        e proteção contra vídeos corrompidos

        Args:
            video_path: Caminho do arquivo de vídeo
            output_path: Caminho de saída para o arquivo WAV
            timeout: Tempo máximo de execução em segundos (None = adaptativo)

        Returns:
            Tuple[bool, str]: (sucesso, mensagem_ou_caminho)
        """
        try:
            logger.info(f"Extraindo áudio de vídeo: {video_path}")
            
            # Calcular timeout adaptativo se não especificado
            if timeout is None:
                timeout = VideoProcessor.calculate_adaptive_timeout(video_path)
            
            # Comando ffmpeg para extrair áudio
            # -i: arquivo de entrada
            # -vn: sem vídeo
            # -acodec pcm_s16le: codec de áudio PCM 16-bit
            # -ar 16000: taxa de amostragem 16kHz (otimizado para Whisper)
            # -ac 1: mono (1 canal)
            # -analyzeduration: limitar análise inicial para detectar hang rápido
            # -probesize: limitar tamanho de probe para vídeos corrompidos
            command = [
                'ffmpeg',
                '-analyzeduration', '10M',  # Limitar análise a 10MB
                '-probesize', '10M',        # Limitar probe a 10MB
                '-i', video_path,
                '-vn',                      # Sem vídeo
                '-acodec', 'pcm_s16le',     # Codec de áudio
                '-ar', '16000',             # Taxa de amostragem
                '-ac', '1',                 # Mono
                '-loglevel', 'error',       # Apenas erros
                '-y',                       # Sobrescrever arquivo
                output_path
            ]
            
            logger.debug(f"Executando ffmpeg com timeout de {timeout}s: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                file_size_mb = file_size / (1024 * 1024)
                
                # Validar que o arquivo tem tamanho mínimo
                if file_size < 1000:  # Mínimo de 1KB
                    logger.error(f"Arquivo WAV extraído muito pequeno ({file_size} bytes) - provavelmente sem áudio")
                    try:
                        os.remove(output_path)
                    except:
                        pass
                    return False, "Vídeo não contém faixa de áudio válida ou está corrompido"
                
                logger.info(f"Áudio extraído com sucesso: {output_path} ({file_size_mb:.2f}MB)")
                return True, output_path
            else:
                error_msg = result.stderr or "Erro desconhecido ao extrair áudio"
                logger.error(f"Erro ao extrair áudio: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired as e:
            # Timeout - limpar arquivo parcial de saída se existir
            logger.error(f"Timeout ao processar vídeo (limite: {timeout}s)")
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    logger.debug(f"Arquivo parcial removido: {output_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Erro ao limpar arquivo parcial: {cleanup_error}")
            
            # subprocess.run() já mata o processo automaticamente no timeout
            return False, f"Timeout ao processar vídeo (limite: {timeout}s). O vídeo pode estar corrompido ou muito grande."
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
