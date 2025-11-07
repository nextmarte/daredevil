"""
BatchAudioProcessor para processamento em paralelo de múltiplos arquivos.
Usa ThreadPoolExecutor para converter áudios/vídeos simultaneamente.
"""
import os
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .audio_processor_optimized import AudioProcessor
from .video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class BatchAudioProcessor:
    """
    ✅ OTIMIZADO: Processa múltiplos áudios/vídeos em paralelo.
    Usa ThreadPoolExecutor para maximizar performance em multi-core.
    """

    # Limita threads para não sobrecarregar I/O
    MAX_WORKERS = min(4, os.cpu_count() or 1)

    @staticmethod
    def process_batch(
        file_paths: List[str],
        is_video: bool = False,
        max_workers: Optional[int] = None
    ) -> List[Dict]:
        """
        ✅ OTIMIZADO: Processa múltiplos arquivos em paralelo.

        Retorna lista de dicts com:
        {
            "file": caminho original,
            "output": caminho convertido,
            "success": bool,
            "error": mensagem de erro (se houver),
            "duration": duração do processamento em segundos
        }

        Args:
            file_paths: Lista de caminhos de arquivos
            is_video: True para processar como vídeos, False para áudio
            max_workers: Número máximo de threads (padrão: 4)

        Returns:
            Lista de resultados do processamento
        """
        import time

        if max_workers is None:
            max_workers = BatchAudioProcessor.MAX_WORKERS

        results = []
        start_batch_time = time.time()

        logger.info(
            f"Iniciando processamento em batch de {len(file_paths)} arquivos "
            f"(max_workers={max_workers}, tipo={'vídeo' if is_video else 'áudio'})"
        )

        if not file_paths:
            logger.warning("Nenhum arquivo para processar")
            return results

        # ✅ OTIMIZADO: ThreadPoolExecutor para paralelização
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Mapear função de processamento baseado no tipo
            if is_video:
                futures = {
                    executor.submit(
                        BatchAudioProcessor._process_video,
                        fp
                    ): fp
                    for fp in file_paths
                }
            else:
                futures = {
                    executor.submit(
                        BatchAudioProcessor._process_audio,
                        fp
                    ): fp
                    for fp in file_paths
                }

            # Coletar resultados conforme completam (não aguarda todos)
            completed = 0
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1

                    # Log de progresso
                    if result["success"]:
                        logger.info(
                            f"✓ [{completed}/{len(file_paths)}] {file_path} "
                            f"convertido em {result['duration']:.2f}s"
                        )
                    else:
                        logger.warning(
                            f"✗ [{completed}/{len(file_paths)}] {file_path}: "
                            f"{result['error']}"
                        )

                except Exception as e:
                    logger.error(f"Erro ao processar {file_path}: {e}")
                    results.append({
                        "file": file_path,
                        "output": None,
                        "success": False,
                        "error": str(e),
                        "duration": 0
                    })
                    completed += 1

        # Resumo do batch
        success_count = sum(1 for r in results if r["success"])
        total_time = time.time() - start_batch_time
        avg_time = total_time / len(file_paths) if file_paths else 0

        logger.info(
            f"✓ Batch concluído: {success_count}/{len(file_paths)} bem-sucedidos "
            f"em {total_time:.2f}s (média: {avg_time:.2f}s/arquivo)"
        )

        return results

    @staticmethod
    def _process_audio(file_path: str) -> Dict:
        """
        Processa um arquivo de áudio individual.

        Args:
            file_path: Caminho do arquivo de áudio

        Returns:
            Dict com resultado do processamento
        """
        import time

        start_time = time.time()

        try:
            logger.debug(f"Processando áudio: {file_path}")

            output_path = AudioProcessor.convert_to_wav(file_path)
            duration = time.time() - start_time

            if output_path:
                return {
                    "file": file_path,
                    "output": output_path,
                    "success": True,
                    "error": None,
                    "duration": duration
                }
            else:
                return {
                    "file": file_path,
                    "output": None,
                    "success": False,
                    "error": "Conversão retornou None",
                    "duration": duration
                }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Erro ao processar áudio {file_path}: {e}")

            return {
                "file": file_path,
                "output": None,
                "success": False,
                "error": str(e),
                "duration": duration
            }

    @staticmethod
    def _process_video(file_path: str) -> Dict:
        """
        Processa um arquivo de vídeo individual (extrai áudio).

        Args:
            file_path: Caminho do arquivo de vídeo

        Returns:
            Dict com resultado do processamento
        """
        import time

        start_time = time.time()

        try:
            logger.debug(f"Processando vídeo: {file_path}")

            # Validar vídeo
            is_valid, error_msg = VideoProcessor.validate_video_file(file_path)
            if not is_valid:
                duration = time.time() - start_time
                return {
                    "file": file_path,
                    "output": None,
                    "success": False,
                    "error": f"Vídeo inválido: {error_msg}",
                    "duration": duration
                }

            # Extrair áudio
            output_path = os.path.join(
                AudioProcessor.TEMP_DIR,
                f"video_extract_{os.urandom(8).hex()}.wav"
            )

            success, msg = VideoProcessor.extract_audio(file_path, output_path)
            duration = time.time() - start_time

            if success:
                return {
                    "file": file_path,
                    "output": output_path,
                    "success": True,
                    "error": None,
                    "duration": duration
                }
            else:
                return {
                    "file": file_path,
                    "output": None,
                    "success": False,
                    "error": f"Extração de áudio falhou: {msg}",
                    "duration": duration
                }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Erro ao processar vídeo {file_path}: {e}")

            return {
                "file": file_path,
                "output": None,
                "success": False,
                "error": str(e),
                "duration": duration
            }

    @staticmethod
    def cleanup_batch_results(results: List[Dict]) -> None:
        """
        Remove arquivos temporários após processamento em batch.

        Args:
            results: Lista de resultados do processamento
        """
        for result in results:
            if result["success"] and result["output"]:
                AudioProcessor.cleanup_temp_file(result["output"])
                logger.debug(f"Temporário removido: {result['output']}")


class ParallelConversionStats:
    """Coleta estatísticas de processamento paralelo."""

    @staticmethod
    def calculate_speedup(
        sequential_time: float,
        parallel_time: float
    ) -> Dict[str, float]:
        """
        Calcula ganho de performance com paralelização.

        Args:
            sequential_time: Tempo de processamento sequencial (segundos)
            parallel_time: Tempo de processamento paralelo (segundos)

        Returns:
            Dict com estatísticas de performance
        """
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        efficiency = (speedup / BatchAudioProcessor.MAX_WORKERS) * 100

        return {
            "sequential_time_s": round(sequential_time, 2),
            "parallel_time_s": round(parallel_time, 2),
            "speedup": round(speedup, 2),
            "efficiency_percent": round(efficiency, 1),
            "workers": BatchAudioProcessor.MAX_WORKERS
        }
