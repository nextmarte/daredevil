# Guia Rápido - Integração LLM Qwen3:30b

## 🚀 Setup em 3 Passos

### 1. Instalar Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Baixar Modelo
```bash
ollama pull qwen3:30b
```
⏱️ Aguarde o download (~17GB, pode levar alguns minutos)

### 3. Iniciar Servidor
```bash
ollama serve
```
✅ Servidor rodando em `http://localhost:11434`

## 🎯 Uso Imediato

### Via API (cURL)
```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@seu_audio.mp3" \
  -F "use_llm=true"
```

### Via Python
```python
from transcription.services import TranscriptionService

result = TranscriptionService.process_audio_file(
    file_path="audio.mp3",
    use_llm=True
)
print(result.transcription.text)
```

### Configuração Permanente
```bash
# No arquivo .env
USE_LLM_POST_PROCESSING=true
LLM_MODEL=qwen3:30b
# OLLAMA_HOST=http://localhost:11434  # Opcional, padrão já é localhost:11434
```

## 🧪 Testar Instalação

```bash
# Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# Executar demo
uv run python demo_llm_post_processing.py
```

## ⚡ Dicas de Performance

### Hardware Recomendado
- **Mínimo:** 16GB RAM, CPU multi-core
- **Ideal:** 32GB RAM, GPU NVIDIA (CUDA)

### Usar Modelo Menor (Mais Rápido)
```bash
# Instalar modelo menor
ollama pull qwen2.5:7b

# Configurar
LLM_MODEL=qwen2.5:7b
```

## 🔧 Solução Rápida de Problemas

### "Connection error"
```bash
# Verificar se Ollama está rodando
ps aux | grep ollama

# Se não estiver, iniciar
ollama serve
```

### "Model not found"
```bash
# Baixar o modelo
ollama pull qwen3:30b

# Listar modelos instalados
ollama list
```

### "Out of memory"
```bash
# Usar modelo menor
ollama pull qwen2.5:3b
LLM_MODEL=qwen2.5:3b
```

## 📊 Comparação Rápida

| Característica | Tradicional | LLM |
|---------------|-------------|-----|
| Velocidade | ⚡⚡⚡ | ⚡⚡ |
| Qualidade | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Requisitos | Baixos | Médios/Altos |
| Offline | ✅ | ✅ |

## 📚 Documentação Completa

- **Detalhes:** [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
- **API:** [README.md](README.md)
- **Testes:** `transcription/test_llm_post_processing.py`

## 💡 Exemplos de Uso

### Transcrição Simples
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@audio.mp3" \
  -F "use_llm=true"
```

### Com Todas as Opções
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@audio.mp3" \
  -F "language=pt" \
  -F "use_llm=true" \
  -F "identify_speakers=true" \
  -F "correct_grammar=true" \
  -F "clean_hesitations=true"
```

### Desabilitar LLM para um Request
```bash
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@audio.mp3" \
  -F "use_llm=false"
```

## ✅ Checklist de Instalação

- [ ] Ollama instalado (`ollama --version`)
- [ ] Modelo baixado (`ollama list | grep qwen3`)
- [ ] Servidor rodando (`curl http://localhost:11434/api/tags`)
- [ ] Variáveis de ambiente configuradas (`.env`)
- [ ] API funcionando (`curl http://localhost:8000/api/health`)
- [ ] Demo executado com sucesso (`uv run python demo_llm_post_processing.py`)

## 🎉 Pronto!

Agora você pode usar o poder do LLM Qwen3:30b para melhorar suas transcrições!

Para mais informações, consulte a [documentação completa](LLM_INTEGRATION.md).
