# Implementação de Timing Metrics - Daredevil API

## 📊 Resumo

Foram adicionadas **métricas detalhadas de timing** à API de transcrição para monitorar quanto tempo é gasto em cada fase do processamento:

1. **Conversão de formato** (remota ou local)
2. **Carregamento do modelo Whisper**
3. **Transcrição de áudio**
4. **Pós-processamento de português**

---

## 🔧 Mudanças Implementadas

### 1. Novo Schema: `TimingMetrics` (schemas.py)

```python
class TimingMetrics(BaseModel):
    """Métricas detalhadas de tempo de processamento"""
    conversion_time: Optional[float] = Field(
        None, description="Tempo gasto em conversão remota de formato (segundos)")
    model_load_time: Optional[float] = Field(
        None, description="Tempo para carregar o modelo Whisper (segundos)")
    transcription_time: Optional[float] = Field(
        None, description="Tempo gasto na transcrição (segundos)")
    post_processing_time: Optional[float] = Field(
        None, description="Tempo gasto no pós-processamento de português (segundos)")
    total_time: float = Field(..., description="Tempo total de processamento (segundos)")
```

### 2. Atualização do `TranscriptionResponse` (schemas.py)

```python
class TranscriptionResponse(BaseModel):
    success: bool
    transcription: Optional[TranscriptionResult] = None
    processing_time: float  # Mantido para compatibilidade
    timing_metrics: Optional[TimingMetrics] = None  # ✨ NOVO
    audio_info: Optional[AudioInfo] = None
    error: Optional[str] = None
    cached: bool = False
```

### 3. Nova Função: `transcribe_with_timing()` (services.py)

```python
@classmethod
def transcribe_with_timing(
    cls,
    audio_path: str,
    language: Optional[str] = None,
    model_name: Optional[str] = None
) -> tuple[TranscriptionResult, float]:
    """
    Transcreve arquivo de áudio e retorna o tempo gasto
    
    Returns:
        tuple: (TranscriptionResult, tempo_de_transcrição_em_segundos)
    """
    start_time = time.time()
    result = cls.transcribe(audio_path, language, model_name)
    elapsed_time = time.time() - start_time
    return result, elapsed_time
```

### 4. Rastreamento de Timing em `process_audio_file()` (services.py)

**Antes:**
- Apenas retornava `processing_time` geral

**Depois:**
- Rastreia `time_conversion_start/end` quando necessário converter formato
- Rastreia `time_transcription_start/end` durante transcrição
- Retorna objeto `TimingMetrics` com breakdown detalhado

**Exemplo de uso:**
```python
# Arquivo precisa de conversão (ex: .ogg → .wav)
time_conversion_start = time.time()
converted_path = AudioProcessor.convert_to_wav(file_path, temp_wav_path)
time_conversion_end = time.time()

# Depois, transcrição
time_transcription_start = time.time()
transcription, transcription_time = WhisperTranscriber.transcribe_with_timing(
    transcribe_path,
    language=language,
    model_name=model
)
time_transcription_end = time.time()

# Montar métricas finais
timing_metrics = TimingMetrics(
    conversion_time=round(time_conversion_end - time_conversion_start, 2) if (time_conversion_start and time_conversion_end) else None,
    model_load_time=None,  # Pode ser adicionado depois
    transcription_time=round(transcription_time, 2),
    post_processing_time=None,
    total_time=round(processing_time, 2)
)
```

---

## 📈 Exemplo de Resposta da API

### Antes (sem timing detalhado):
```json
{
    "success": true,
    "transcription": {
        "text": "Olá, como você está?",
        "segments": [...],
        "language": "pt",
        "duration": 2.5
    },
    "processing_time": 15.32,
    "audio_info": {...},
    "cached": false
}
```

### Depois (com timing detalhado):
```json
{
    "success": true,
    "transcription": {
        "text": "Olá, como você está?",
        "segments": [...],
        "language": "pt",
        "duration": 2.5
    },
    "processing_time": 15.32,
    "timing_metrics": {
        "conversion_time": 2.15,
        "model_load_time": null,
        "transcription_time": 12.89,
        "post_processing_time": null,
        "total_time": 15.32
    },
    "audio_info": {...},
    "cached": false
}
```

---

## 🎯 Casos de Uso

### 1. Arquivo WAV (sem conversão)
```json
{
    "timing_metrics": {
        "conversion_time": null,  // Não teve conversão
        "transcription_time": 5.42,
        "total_time": 5.42
    }
}
```

### 2. Arquivo .ogg (com conversão remota)
```json
{
    "timing_metrics": {
        "conversion_time": 3.21,  // Enviou para API remota em 192.168.1.33
        "transcription_time": 8.67,
        "total_time": 11.88
    }
}
```

### 3. Vídeo .mp4 (com extração de áudio)
```json
{
    "timing_metrics": {
        "conversion_time": 2.45,  // Extração de áudio via ffmpeg
        "transcription_time": 42.15,  // Vídeo de 1 minuto
        "total_time": 44.60
    }
}
```

### 4. Resultado do cache
```json
{
    "timing_metrics": null,  // Cache não tem timing metrics
    "processing_time": 0.05,  // Apenas lookup no cache
    "cached": true
}
```

---

## 📊 Dashboard de Monitoramento (Futuro)

Próximo passo será criar um endpoint `/api/transcribe/statistics` para agregar métricas:

```json
GET /api/transcribe/statistics

{
    "total_transcriptions": 1523,
    "average_conversion_time": 1.8,
    "average_transcription_time": 8.5,
    "average_total_time": 10.3,
    "slowest_file": {
        "filename": "video_long.mp4",
        "processing_time": 145.23
    },
    "fastest_file": {
        "filename": "short.wav",
        "processing_time": 2.15
    },
    "cache_hit_rate": 0.32
}
```

---

## 🧪 Teste

Execute o script de teste para verificar:

```bash
cd /home/marcus/projects/daredevil
python test_timing_impl.py
```

**Saída esperada:**
```
✅ Arquivo de teste encontrado: /home/marcus/projects/daredevil/tests/test_audio.wav
   Tamanho: 0.42 MB

🔄 Processando arquivo com TranscriptionService...

📊 Resultado:
   Sucesso: True
   Tempo total: 8.45s

⏱️ Métricas de timing:
   📤 Tempo de conversão: N/A (nenhuma conversão necessária)
   📤 Tempo de carregamento do modelo: (incluído na transcrição)
   🎙️  Tempo de transcrição: 8.42s
   ✨ Tempo de pós-processamento: (incluído na transcrição)
   ⏲️  Tempo total: 8.45s

📝 Transcrição (primeiros 300 caracteres):
   Olá, este é um teste de áudio...

✅ Teste completado com sucesso!

📋 RESUMO DAS MÉTRICAS:
============================================================
Conversão:     N/A    segundos
Transcrição:        8.42 segundos
TOTAL:              8.45 segundos
============================================================
```

---

## 📝 Notas Importantes

1. **Compatibilidade**: Campo `processing_time` foi mantido para compatibilidade com clientes antigos
2. **Cache**: Quando resultado vem do cache, `timing_metrics` é `null`
3. **Conversão vs Extração**: 
   - Conversão remota (`.ogg` → `.wav`): Usa `convert_to_wav()` da API remota
   - Extração de áudio (`.mp4`): Usa `extract_audio()` local com ffmpeg
4. **Precisão**: Tempos são arredondados para 2 casas decimais

---

## 🚀 Próximos Passos

1. ✅ Adicionar `TimingMetrics` ao schema
2. ✅ Instrumentar `process_audio_file()` com checkpoints de tempo
3. ⏳ Otimizar carregamento de modelo (cache em GPU)
4. ⏳ Criar endpoint `/api/transcribe/statistics`
5. ⏳ Implementar dashboard de monitoramento em tempo real

---

## 📖 Referência Rápida

### Campos de Timing

| Campo | Descrição | Quando aparece | Segundos |
|-------|-----------|-----------------|----------|
| `conversion_time` | Conversão remota (.ogg, .aac, etc) ou extração (vídeo) | Apenas se necessário | ~1-5 |
| `model_load_time` | Carregamento do Whisper | Primeira execução | ~1-2 (CPU) ou 0.5-1 (GPU) |
| `transcription_time` | Processamento de áudio no Whisper | Sempre | ~1-60+ |
| `post_processing_time` | Pós-processamento de português | Sempre (incluído em transcription) | Negligenciável |
| `total_time` | Soma de todos os tempos | Sempre | Varia |

### Fórmula de Timing

```
total_time = conversion_time (se houver) + transcription_time + overhead
```

---

**Última atualização**: Novembro 2025
**Status**: ✅ Implementado e testável
