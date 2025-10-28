# Integração LLM com Qwen3:30b

## 📋 Visão Geral

Este documento descreve a integração do modelo LLM Qwen3:30b (via Ollama) para pós-processamento avançado de transcrições de áudio. O LLM oferece correções mais precisas e inteligentes comparado ao processamento tradicional baseado em regras.

## 🎯 Vantagens do Pós-Processamento com LLM

### Comparação: LLM vs. Tradicional

| Recurso | Processamento Tradicional | Processamento LLM (Qwen3:30b) |
|---------|---------------------------|--------------------------------|
| **Correção Gramatical** | Baseada em regras (LanguageTool) | Compreensão contextual profunda |
| **Identificação de Interlocutores** | Heurísticas (pausas, perguntas) | Análise semântica do contexto |
| **Remoção de Hesitações** | Regex patterns | Compreensão do fluxo natural da fala |
| **Correção de Gírias** | Limitada | Excelente |
| **Qualidade Geral** | Boa | Excepcional |
| **Velocidade** | Muito rápida (~1s) | Moderada (~5-15s dependendo do tamanho) |
| **Requisitos** | Conexão internet (LanguageTool) | Ollama rodando localmente |

## 🚀 Instalação

### Pré-requisitos

1. **Instalar Ollama**
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Ou baixe em: https://ollama.ai/download
   ```

2. **Baixar o modelo Qwen3:30b**
   ```bash
   ollama pull qwen3:30b
   ```
   
   > ⚠️ **Nota:** O modelo tem aproximadamente 17GB. Certifique-se de ter espaço em disco suficiente.

3. **Iniciar o servidor Ollama**
   ```bash
   ollama serve
   ```
   
   O servidor ficará disponível em `http://localhost:11434`

### Requisitos de Hardware

- **RAM:** Mínimo 16GB recomendado (32GB ideal para o modelo 30b)
- **Disco:** ~20GB de espaço livre
- **CPU/GPU:** GPU com CUDA é recomendada mas não obrigatória

## ⚙️ Configuração

### Variáveis de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# Habilitar pós-processamento LLM por padrão
USE_LLM_POST_PROCESSING=true

# Modelo LLM a ser usado
LLM_MODEL=qwen3:30b

# URL do servidor Ollama
OLLAMA_URL=http://localhost:11434/api/generate
```

### Configuração Alternativa

Se preferir não usar LLM por padrão:

```bash
# Manter processamento tradicional como padrão
USE_LLM_POST_PROCESSING=false
```

E habilitar LLM por requisição via API (parâmetro `use_llm=true`).

## 📖 Uso

### Via API

#### Endpoint: POST /api/transcribe

**Com LLM habilitado:**

```bash
curl -X POST "http://localhost:8000/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt" \
  -F "use_llm=true" \
  -F "identify_speakers=true" \
  -F "correct_grammar=true"
```

**Resposta exemplo:**

```json
{
  "success": true,
  "transcription": {
    "text": "Pessoa 1: Olá, tudo bem?\nPessoa 2: Sim, estou bem. E você?\nPessoa 1: Também estou bem, obrigado.",
    "segments": [
      {
        "start": 0.0,
        "end": 2.0,
        "text": "Olá, tudo bem?",
        "original_text": "ola tudo bem",
        "speaker_id": "Pessoa 1",
        "confidence": 0.95
      },
      {
        "start": 2.5,
        "end": 4.5,
        "text": "Sim, estou bem. E você?",
        "original_text": "sim to bem e vc",
        "speaker_id": "Pessoa 2",
        "confidence": 0.92
      }
    ],
    "formatted_conversation": "Pessoa 1: Olá, tudo bem?\nPessoa 2: Sim, estou bem. E você?\nPessoa 1: Também estou bem, obrigado.",
    "post_processed": true
  }
}
```

### Via Código Python

```python
from transcription.services import TranscriptionService

# Processar áudio com LLM
result = TranscriptionService.process_audio_file(
    file_path="audio.mp3",
    language="pt",
    use_llm=True,  # Habilitar LLM
    correct_grammar=True,
    identify_speakers=True,
    clean_hesitations=True
)

print(result.transcription.text)
print(result.transcription.formatted_conversation)
```

### Script de Demonstração

Execute o script de demonstração incluído:

```bash
uv run python demo_llm_post_processing.py
```

Este script mostra:
- Verificação da conexão com Ollama
- Correção gramatical avançada
- Identificação inteligente de interlocutores
- Remoção de hesitações
- Exemplos práticos de uso

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes de pós-processamento
uv run python -m unittest transcription.test_post_processing -v

# Apenas testes LLM
uv run python -m unittest transcription.test_llm_post_processing -v
```

### Cobertura de Testes

Os testes LLM incluem:
- ✅ Inicialização do serviço
- ✅ Construção de prompts
- ✅ Processamento bem-sucedido
- ✅ Identificação de interlocutores
- ✅ Tratamento de erros (timeout, conexão)
- ✅ Parsing de diferentes formatos de marcadores
- ✅ Pipeline completo de integração

## 🔧 Solução de Problemas

### Erro: "Connection error" ou "Cannot connect to Ollama"

**Causa:** Ollama não está rodando ou não está acessível.

**Solução:**
```bash
# Verificar se Ollama está rodando
curl http://localhost:11434/api/tags

# Se não estiver, inicie o servidor
ollama serve
```

### Erro: "Model not found: qwen3:30b"

**Causa:** O modelo não foi baixado.

**Solução:**
```bash
ollama pull qwen3:30b
```

### Processamento Muito Lento

**Causa:** Hardware limitado ou modelo muito grande.

**Soluções:**
1. Use uma GPU com CUDA se disponível
2. Considere usar um modelo menor (mais rápido):
   ```bash
   ollama pull qwen2.5:7b
   ```
   E configure:
   ```bash
   LLM_MODEL=qwen2.5:7b
   ```

### Fallback Automático

Se o LLM falhar (timeout, erro de conexão, etc), o sistema automaticamente:
1. Registra o erro no log
2. Retorna a transcrição original sem processamento
3. Continua funcionando normalmente

## 📊 Performance

### Benchmarks Típicos

| Duração do Áudio | Tempo de Transcrição (Whisper) | Tempo LLM (Qwen3:30b) | Total |
|------------------|--------------------------------|----------------------|-------|
| 10 segundos | ~2s | ~5s | ~7s |
| 30 segundos | ~5s | ~8s | ~13s |
| 1 minuto | ~8s | ~12s | ~20s |
| 5 minutos | ~30s | ~25s | ~55s |

> **Nota:** Tempos variam baseado em hardware. GPU acelera significativamente.

## 🎯 Casos de Uso Recomendados

### Quando Usar LLM:

✅ **Conversas importantes** - reuniões, entrevistas
✅ **Múltiplos interlocutores** - identificação mais precisa
✅ **Áudio com muitos erros** - correções mais inteligentes
✅ **Gírias e linguagem informal** - melhor compreensão
✅ **Qualidade final importa mais que velocidade**

### Quando Usar Processamento Tradicional:

✅ **Processamento em tempo real** - muito mais rápido
✅ **Grande volume de áudios** - menor uso de recursos
✅ **Hardware limitado** - não requer GPU
✅ **Áudio já de boa qualidade** - diferença mínima

## 🔐 Segurança e Privacidade

### Dados Locais

- ✅ Todo processamento ocorre localmente via Ollama
- ✅ Nenhum dado é enviado para servidores externos
- ✅ Sem necessidade de API keys ou autenticação externa
- ✅ Totalmente offline (após download do modelo)

## 🚀 Próximos Passos

### Melhorias Planejadas

1. **Suporte a múltiplos modelos**
   - Permitir escolha do modelo via API
   - Suporte a modelos especializados por domínio

2. **Cache inteligente**
   - Cachear correções frequentes
   - Reduzir tempo de processamento para áudios similares

3. **Processamento em lote otimizado**
   - Processar múltiplos áudios em paralelo
   - Melhor uso de GPU

4. **Fine-tuning**
   - Treinar modelo específico para português brasileiro
   - Melhorar identificação de sotaques regionais

## 📚 Recursos Adicionais

- [Documentação Ollama](https://github.com/ollama/ollama)
- [Modelo Qwen](https://github.com/QwenLM/Qwen)
- [API Daredevil](README.md)

## 💡 Exemplos de Transformações

### Antes (Transcrição Bruta):
```
ola tudo bem com vc ah sim to bem e vc tambem to legal vamos comecar entao
```

### Depois (LLM - Qwen3:30b):
```
Pessoa 1: Olá, tudo bem com você?
Pessoa 2: Sim, estou bem. E você?
Pessoa 1: Também estou legal. Vamos começar então.
```

## 🤝 Contribuindo

Encontrou um bug ou tem uma sugestão? Abra uma issue no GitHub!

## 📄 Licença

Este projeto está sob a mesma licença do projeto Daredevil principal.

---

**Desenvolvido com ❤️ para melhorar a transcrição de áudio em português usando IA**
