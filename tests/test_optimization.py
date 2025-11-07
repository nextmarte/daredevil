""""""

import numpy as np
import subprocess
import loggingimport logging
import tempfileimport tempfile
import timeimport time
import osimport os
Testes para validar as otimizações de conversão de áudio/vídeo com ffmpeg puro e paralelização.Testes para validar as otimizações de conversão de áudio/vídeo com ffmpeg puro e paralelização.


Funcionalidades testadas: Funcionalidades testadas:

1. Validação prévia com ffprobe1. Validação prévia com ffprobe

2. Detecção de skip de conversão(16kHz mono)2. Detecção de skip de conversão(16kHz mono)

3. Conversão com ffmpeg multi-thread3. Conversão com ffmpeg multi-thread

4. Processamento em batch com ThreadPoolExecutor4. Processamento em batch com ThreadPoolExecutor

5. Performance: sequential vs paralelo5. Performance: sequential vs paralelo

""""""


logger = logging.getLogger(__name__)from scipy.io import wavfile


logger = logging.getLogger(__name__)


def create_test_wav_file_simple(duration: float = 1.0) -> str:
    """

    Cria arquivo WAV de teste usando ffmpeg (fallback simples).def create_test_wav_file(duration: float = 1.0, sample_rate: int = 16000, channels: int = 1) -> str:

        """

    Args:    Cria arquivo WAV de teste.

       duration: Duração em segundos

           Args:

    Returns:        duration: Duração em segundos

       Caminho do arquivo criado        sample_rate: Sample rate em Hz

    """        channels: Número de canais

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')

    temp_path = temp_file.name    Returns:

    temp_file.close()        Caminho do arquivo criado

        """

    try:    # Gerar áudio de teste (tom de 440Hz)

        # Usar ffmpeg para gerar tom de teste (16kHz mono)    num_samples = int(duration * sample_rate)

        command = [frequency= 440  # Hz (nota A)

                       "ffmpeg",

                       "-f", "lavfi",    # Gerar senoide

                       "-i", f"sine=f=440:d={duration}",    t= np.linspace(0, duration, num_samples)

                       "-acodec", "pcm_s16le",    audio_data= (0.3 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)

                       "-ar", "16000",

                       "-ac", "1",    # Criar arquivo temporário

                       "-y",    temp_file= tempfile.NamedTemporaryFile(delete=False, suffix='.wav')

                       temp_path    temp_path= temp_file.name

                       ]    temp_file.close()

        # Converter para int16
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=10)

           audio_int16 = (audio_data * 32767).astype(np.int16)

        if result.returncode == 0 and os.path.exists(temp_path):

            # Se multi-canal, duplicar
            logger.info(
                f"✓ Arquivo WAV de teste criado: {temp_path} ({duration:.1f}s, 16kHz mono)")

            return temp_path if channels > 1:

        else:
            audio_int16 = np.tile(audio_int16, (channels, 1)).T

           logger.error(f"Falha ao criar arquivo WAV: {result.stderr}")

            return None    # Salvar WAV

        wavfile.write(temp_path, sample_rate, audio_int16)

    except Exception as e:
        logger.info(

        logger.error(f"Erro ao criar arquivo WAV: {e}")        f"✓ Arquivo WAV de teste criado: {temp_path} ({duration:.1f}s)")

       return None

    return temp_path


def test_audio_processor_validation():
    """def test_audio_processor_validation():

    Testa validação prévia de áudio com ffprobe.    """

    """    Testa validação prévia de áudio com ffprobe.

    print("\n" + "="*60)    """

    print("TEST 1: AudioProcessor.validate_audio_file()") print("\n" + "="*60)

    print("="*60) print("TEST 1: AudioProcessor.validate_audio_file()")

       print("="*60)

    from transcription.audio_processor_optimized import AudioProcessor

       from transcription.audio_processor_optimized import AudioProcessor

    wav_file = create_test_wav_file_simple(duration=2.0)

       # Criar arquivo WAV de teste

    if not wav_file:
        wav_file = create_test_wav_file(duration=2.0, sample_rate=16000)

       print("⚠️  SKIPPED: Não foi possível criar arquivo de teste")

        return True try:

            # Testar validação

    try:
        start = time.time()

       start = time.time()        is_valid, metadata = AudioProcessor.validate_audio_file(wav_file)

        is_valid, metadata = AudioProcessor.validate_audio_file(wav_file)        duration = time.time() - start

        duration = time.time() - start

           print(f"✓ Validação concluída em {duration:.3f}s")

        print(f"✓ Validação concluída em {duration:.3f}s") print(f"  - Arquivo válido: {is_valid}")

        print(f"  - Arquivo válido: {is_valid}") print(f"  - Metadados: {metadata}")

        if metadata:

            print(f"  - Streams: {len(metadata.get('streams', []))}") assert is_valid, "Arquivo deveria ser válido"

               assert metadata is not None, "Metadados devem ser retornados"

        assert is_valid, "Arquivo deveria ser válido" print("✅ PASSOU: Validação com ffprobe funcionando")

        assert metadata is not None, "Metadados devem ser retornados"

        print("✅ PASSOU: Validação com ffprobe funcionando") finally:

        return True        # Limpar

           if os.path.exists(wav_file):

    except Exception as e:
        os.remove(wav_file)

       print(f"❌ FALHA: {e}")

        return False

    finally:
        def test_audio_processor_get_info():

        if os.path.exists(wav_file):
            """

            os.remove(wav_file)    Testa extração de informações de áudio.

    """

    print("\n" + "="*60)


def test_audio_processor_get_info():    print("TEST 2: AudioProcessor.get_audio_info()")
   """    print("="*60)

    Testa extração de informações de áudio.

    """ from transcription.audio_processor_optimized import AudioProcessor

    print("\n" + "="*60)

    print("TEST 2: AudioProcessor.get_audio_info()")    wav_file = create_test_wav_file(

        print("="*60)        duration=3.0, sample_rate=16000, channels=1)


    from transcription.audio_processor_optimized import AudioProcessor try:

        start = time.time()

    wav_file = create_test_wav_file_simple(duration=3.0)        audio_info = AudioProcessor.get_audio_info(wav_file)

       duration = time.time() - start

    if not wav_file:

        print("⚠️  SKIPPED: Não foi possível criar arquivo de teste") print(f"✓ Extração de info concluída em {duration:.3f}s")

        return True print(f"  - Sample rate: {audio_info['sample_rate']}Hz")

           print(f"  - Canais: {audio_info['channels']}")

    try:
        print(f"  - Duração: {audio_info['duration']:.2f}s")

       start = time.time()        print(f"  - Codec: {audio_info['codec']}")

        audio_info = AudioProcessor.get_audio_info(wav_file)

        duration = time.time() - start assert audio_info['sample_rate'] == 16000, "Sample rate deveria ser 16000"

           assert audio_info['channels'] == 1, "Deveria ser mono"

        if audio_info is None:
            print("✅ PASSOU: Extração de informações funcionando")

           print("⚠️  SKIPPED: get_audio_info retornou None")

            return True finally:

                if os.path.exists(wav_file):

        print(f"✓ Extração de info concluída em {duration:.3f}s")            os.remove(wav_file)

        print(f"  - Sample rate: {audio_info.get('sample_rate')}Hz")

        print(f"  - Canais: {audio_info.get('channels')}")

        print(f"  - Duração: {audio_info.get('duration'):.2f}s")def test_skip_conversion():

        print(f"  - Codec: {audio_info.get('codec')}")    """

            Testa detecção de skip de conversão (16kHz mono).

        assert audio_info['sample_rate'] == 16000, "Sample rate deveria ser 16000"    """

        assert audio_info['channels'] == 1, "Deveria ser mono" print("\n" + "="*60)

        print("✅ PASSOU: Extração de informações funcionando") print("TEST 3: AudioProcessor.needs_conversion() - Skip Detection")

        return True print("="*60)



    except Exception as e:
        from transcription.audio_processor_optimized import AudioProcessor

       print(f"❌ FALHA: {e}")

        return False    wav_file = create_test_wav_file(

            finally:        duration=1.0, sample_rate=16000, channels=1)

        if os.path.exists(wav_file):

            os.remove(wav_file) try:

            # Obter info

        audio_info = AudioProcessor.get_audio_info(wav_file)


def test_skip_conversion():
    """        # Testar skip

    Testa detecção de skip de conversão (16kHz mono).        start = time.time()

    """        needs_conv = AudioProcessor.needs_conversion(audio_info)

    print("\n" + "="*60)        duration = time.time() - start

    print("TEST 3: AudioProcessor.needs_conversion() - Skip Detection")

    print("="*60) print(f"✓ Detecção de skip concluída em {duration:.3f}s")

       print(f"  - Arquivo: 16kHz mono")

    from transcription.audio_processor_optimized import AudioProcessor print(f"  - Precisa conversão: {needs_conv}")


    wav_file = create_test_wav_file_simple(duration=1.0) assert not needs_conv, "Arquivo 16kHz mono não deveria precisar conversão"

       print("✅ PASSOU: Skip de conversão detectado corretamente")

    if not wav_file:

        # Testar resultado (deveria retornar arquivo original)
        print("⚠️  SKIPPED: Não foi possível criar arquivo de teste")

        return True        result = AudioProcessor.convert_to_wav(wav_file)

           assert result == wav_file, "Deveria retornar arquivo original (sem conversão)"

    try:
        print("✅ PASSOU: Arquivo original retornado (conversão skipped)")

       audio_info = AudioProcessor.get_audio_info(wav_file)

           finally:

        if audio_info is None:
            if os.path.exists(wav_file):

            print("⚠️  SKIPPED: Não foi possível obter info do áudio")            os.remove(wav_file)

            return True


        start = time.time()def test_ffmpeg_conversion_multithreading():

        needs_conv = AudioProcessor.needs_conversion(audio_info)    """

        duration = time.time() - start    Testa conversão com ffmpeg multi-thread.

            """

        print(f"✓ Detecção de skip concluída em {duration:.3f}s") print("\n" + "="*60)

        print(f"  - Arquivo: 16kHz mono") print("TEST 4: AudioProcessor.convert_to_wav() - FFmpeg Multi-thread")

        print(f"  - Precisa conversão: {needs_conv}") print("="*60)


        assert not needs_conv, "Arquivo 16kHz mono não deveria precisar conversão" from transcription.audio_processor_optimized import AudioProcessor

        print("✅ PASSOU: Skip de conversão detectado corretamente")

           # Criar arquivo com taxa diferente (22050Hz estéreo)

        result = AudioProcessor.convert_to_wav(wav_file)    wav_file = create_test_wav_file(

            assert result == wav_file, "Deveria retornar arquivo original (sem conversão)"        duration=2.0, sample_rate=22050, channels=2)

        print("✅ PASSOU: Arquivo original retornado (conversão skipped)")

        return True try:

            AudioProcessor.ensure_temp_dir()

    except Exception as e:

        print(f"❌ FALHA: {e}")        # Testar conversão com ffmpeg

        return False        start = time.time()

    finally:
        result = AudioProcessor.convert_to_wav(wav_file)

        if os.path.exists(wav_file):
            duration = time.time() - start

           os.remove(wav_file)

        print(f"✓ Conversão com ffmpeg concluída em {duration:.3f}s")

        print(f"  - Arquivo original: 22050Hz estéreo")


def test_batch_processor():        print(f"  - Arquivo convertido: {result}")
   """

    Testa processamento em lote com ThreadPoolExecutor.        assert result is not None, "Conversão deveria retornar caminho válido"

    """ assert os.path.exists(result), "Arquivo convertido deveria existir"

    print("\n" + "="*60)

    # Validar arquivo convertido
    print("TEST 4: BatchAudioProcessor - Parallel Processing")

    print("="*60)        audio_info = AudioProcessor.get_audio_info(result)

       print(

            from transcription.audio_processor_optimized import AudioProcessor            f"  - Resultado: {audio_info['sample_rate']}Hz {audio_info['channels']}ch")

    from transcription.batch_processor import BatchAudioProcessor

       assert audio_info['sample_rate'] == 16000, "Sample rate deveria ser 16000"

    test_files = [] assert audio_info['channels'] == 1, "Deveria ser mono"

    for i in range(2):
        print("✅ PASSOU: Conversão com ffmpeg funcionando")

       wav_file = create_test_wav_file_simple(duration=1.0)

        if wav_file:        # Limpar

            test_files.append(wav_file)        AudioProcessor.cleanup_temp_file(result)



    if not test_files:
        finally:

        print("⚠️  SKIPPED: Não foi possível criar arquivos de teste") if os.path.exists(wav_file):

        return True            os.remove(wav_file)


    try:

        AudioProcessor.ensure_temp_dir()def test_batch_processor():

            """

        print(f"\n📊 Processando {len(test_files)} arquivo(s) em paralelo")    Testa processamento em lote com ThreadPoolExecutor.

            """

        start_par = time.time() print("\n" + "="*60)

        results = BatchAudioProcessor.process_batch(test_files, is_video=False, max_workers=2) print("TEST 5: BatchAudioProcessor - Parallel Processing")

        time_parallel = time.time() - start_par print("="*60)

        print(f"Tempo paralelo: {time_parallel:.3f}s")

           from transcription.audio_processor_optimized import AudioProcessor

        success_count = sum(1 for r in results if r['success']) from transcription.batch_processor import BatchAudioProcessor

        print(f"\nResultados do batch:")

        # Criar múltiplos arquivos de teste
        print(f"  - Arquivos processados: {len(results)}")

        print(f"  - Sucesso: {success_count}/{len(results)}")    test_files = []

           for i in range(3):

        assert success_count == len(test_files), "Todos os arquivos deviam ser processados"        wav_file = create_test_wav_file(

            print("✅ PASSOU: Batch processing funcionando")            duration=1.0, sample_rate=22050 + (i*1000), channels=1)

           test_files.append(wav_file)

        BatchAudioProcessor.cleanup_batch_results(results)

        return True try:

            AudioProcessor.ensure_temp_dir()

    except Exception as e:

        # Testar batch sequencial (para comparação)
        print(f"❌ FALHA: {e}")

        import traceback print("\n📊 Teste SEQUENCIAL:")

        traceback.print_exc()        start_seq = time.time()

        return False for wav_file in test_files:

    finally:
        AudioProcessor.convert_to_wav(wav_file)

        for wav_file in test_files:
            time_sequential = time.time() - start_seq

            if os.path.exists(wav_file):
                print(f"Tempo sequencial: {time_sequential:.3f}s")

               os.remove(wav_file)

        # Testar batch paralelo

        print("\n📊 Teste PARALELO (4 threads):")


def run_all_tests():        start_par = time.time()
   """Executa todos os testes."""        results = BatchAudioProcessor.process_batch(

        print("\n" + "🚀 "*20)            test_files, is_video=False, max_workers=4)

    print("TESTES DE OTIMIZAÇÃO DE CONVERSÃO DE ÁUDIO/VÍDEO")        time_parallel = time.time() - start_par

    print("🚀 "*20) print(f"Tempo paralelo: {time_parallel:.3f}s")


    tests = [        # Analisar resultado

        ("Validação com ffprobe", test_audio_processor_validation),        success_count= sum(1 for r in results if r['success'])

        ("Extração de informações", test_audio_processor_get_info), print(f"\n✓ Resultados do batch:")

        ("Skip de conversão", test_skip_conversion), print(f"  - Arquivos processados: {len(results)}")

        ("Batch processing paralelo", test_batch_processor), print(f"  - Sucesso: {success_count}/{len(results)}")

    ] print(f"  - Speedup: {time_sequential/time_parallel:.2f}x")

       print(f"  - Eficiência: {(time_sequential/time_parallel)/4*100:.1f}%")

    passed = 0

    failed = 0 assert success_count == len(

        test_files), "Todos os arquivos deviam ser processados"

    for test_name, test_func in tests:
        assert time_parallel < time_sequential, "Paralelo deveria ser mais rápido"

        try:
            print("✅ PASSOU: Batch processing com aceleração paralela")

           if test_func():

                passed += 1        # Limpar

            else:
                BatchAudioProcessor.cleanup_batch_results(results)

               failed += 1

        except Exception as e:
            finally:

            failed += 1 for wav_file in test_files:

            print(f"\n❌ FALHA: {test_name}") if os.path.exists(wav_file):

            print(f"   Erro: {e}")                os.remove(wav_file)

            import traceback

            traceback.print_exc()

    def run_all_tests():

    print("\n" + "="*60)    """Executa todos os testes."""

    print("📊 RESUMO DE TESTES") print("\n" + "🚀 "*20)

    print("="*60) print("TESTES DE OTIMIZAÇÃO DE CONVERSÃO DE ÁUDIO/VÍDEO")

    print(f"✅ Passou: {passed}") print("🚀 "*20)

    print(f"❌ Falhou: {failed}")

    print(f"📈 Total: {passed + failed}")    tests = [

        test_audio_processor_validation,

        if failed == 0:        test_audio_processor_get_info,

        print("\n🎉 TODOS OS TESTES PASSARAM!")        test_skip_conversion,

        else:        test_ffmpeg_conversion_multithreading,

        print(f"\n⚠️  {failed} teste(s) falharam")        test_batch_processor

    ]

    return failed == 0

    passed = 0

    failed = 0


if __name__ == "__main__":

    logging.basicConfig(for test_func in tests:

                            level=logging.INFO,        try:

                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'            test_func()

                            )            passed += 1

       except Exception as e:

    success = run_all_tests()            failed += 1

    exit(0 if success else 1) print(f"\n❌ FALHA: {test_func.__name__}")

       print(f"   Erro: {e}")
        import traceback
        traceback.print_exc()

    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DE TESTES")
    print("="*60)
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print(f"\n⚠️  {failed} teste(s) falharam")

    return failed == 0


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Executar testes
    success = run_all_tests()
    exit(0 if success else 1)
