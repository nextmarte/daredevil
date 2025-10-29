# 🇧🇷 Suporte a Português Brasileiro - Daredevil API

Documento detalhando as otimizações e funcionalidades para português brasileiro.

## 📝 Visão Geral

A Daredevil API foi totalmente otimizada para suportar português brasileiro como **idioma padrão** de transcrição. Isso inclui:

- ✅ Português como linguagem padrão automática
- ✅ Pós-processamento de texto específico para português
- ✅ Remoção de hesitações comuns em português
- ✅ Correções de pontuação e capitalização
- ✅ Expansão de abreviações portuguesas
- ✅ Otimizações do Whisper para português

## 🎯 Características de Português Brasileiro

### 1. **Linguagem Padrão**
Todos os endpoints assumem português como idioma padrão:

```bash
# Sem especificar linguagem (usa português)
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3"

# Explicitamente português
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=pt"

# Outro idioma
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=en"
```

### 2. **Pós-Processamento de Texto**

O sistema automaticamente processa o texto transcrito para melhorar qualidade:

#### a) **Remoção de Hesitações**
Remove hesitações comuns do português falado:
- "tipo", "sabe", "entendeu", "né", "tá"
- "hã", "hm", "hmm", "ah", "é"
- E outras hesitações comuns

```python
# Entrada (do Whisper):
"Então tipo, você sabe, isso é bem importante, né"

# Saída (processada):
"Então, você sabe, isso é bem importante"
```

#### b) **Pontuação Normalizada**
- Remove espaços antes de pontuação
- Adiciona espaço após pontuação
- Corrige múltiplas pontuações (... → ...)

```python
# Entrada:
"O texto tem espaço errado , antes de vírgula"

# Saída:
"O texto tem espaço errado, antes de vírgula"
```

#### c) **Capitalização Correta**
- Primeira letra do texto maiúscula
- Primeira letra após pontuação final
- Nomes próprios reconhecidos

```python
# Entrada:
"joão mora em são paulo. ele trabalha na costa."

# Saída:
"João mora em São Paulo. Ele trabalha na Costa."
```

#### d) **Expansão de Abreviações**
Expande abreviações comuns em português:

```python
# Entrada:
"O sr joão e a sra maria trabalham na ltda."

# Saída:
"O Sr. João e a Sra. Maria trabalham na Ltda."
```

### 3. **Correção de Erros Comuns**
Corrige erros típicos do Whisper em português:

- Acentuação incorreta
- Crase mal colocada
- Palavras mal separadas (de o → do, em a → na, etc.)

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Idioma padrão para Whisper
WHISPER_LANGUAGE=pt

# Modelo Whisper (recomendado: medium ou large para português)
WHISPER_MODEL=medium

# Locale do sistema (para formatação de datas/números)
LANGUAGE=pt_BR.UTF-8
LANG=pt_BR.UTF-8
LC_ALL=pt_BR.UTF-8
```

### No docker-compose.yml

```yaml
environment:
  - WHISPER_LANGUAGE=pt
  - WHISPER_MODEL=medium
  - LANGUAGE=pt_BR.UTF-8
  - LANG=pt_BR.UTF-8
  - LC_ALL=pt_BR.UTF-8
```

## 📊 Exemplo de Uso Completo

### 1. Transcrever áudio em português (padrão)

```bash
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@mensagem_whatsapp.opus" \
  -F "model=medium"
```

### 2. Resposta

```json
{
  "success": true,
  "transcription": {
    "text": "Olá João, tudo bem? Você pode me ligar quando chegar em casa?",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Olá João, tudo bem?",
        "confidence": 0.95
      },
      {
        "start": 2.5,
        "end": 5.0,
        "text": "Você pode me ligar quando chegar em casa?",
        "confidence": 0.92
      }
    ],
    "language": "pt",
    "duration": 5.0
  },
  "processing_time": 8.32,
  "audio_info": {
    "format": "opus",
    "duration": 5.0,
    "sample_rate": 48000,
    "channels": 1,
    "file_size_mb": 0.15
  }
}
```

### 3. Testar processamento

```bash
# Script de teste em português
python test_portuguese_br.py
```

## 🔧 Personalizações Possíveis

### Adicionar novas hesitações

Edite `config/settings.py`:

```python
PORTUGUESE_BR_CONFIG = {
    # ...
    'hesitations': [
        'hã', 'hm', 'hmm', 'ah', 'é', 'tipo', 'sabe', 'entendeu',
        'né', 'tá', 'ahn', 'mm', 'huh', 'hun', 'shh',
        # Adicione aqui:
        'blá', 'bla', 'ai'
    ],
}
```

### Adicionar abreviações

Edite `config/settings.py`:

```python
PORTUGUESE_BR_CONFIG = {
    # ...
    'abbreviations': {
        # ...
        'pg': 'Pág.',
        'obs': 'Obs.',
        'approx': 'Aprox.'
    }
}
```

### Desabilitar pós-processamento

No código, você pode desabilitar:

```python
from transcription.portuguese_processor import PortugueseBRTextProcessor

# Apenas remove hesitações
text = PortugueseBRTextProcessor.process(
    text,
    remove_hesitations=True,
    expand_abbreviations=False
)

# Ou fazer processamento customizado
text = PortugueseBRTextProcessor.remove_hesitations(text)
text = PortugueseBRTextProcessor.normalize_punctuation(text)
```

## 📈 Performance em Português

### Modelo Recomendado

- **Desenvolvimento/Testes**: `small` (rápido, qualidade boa)
- **Produção**: `medium` ou `large` (qualidade excelente)

### Tempos Esperados (com GPU)

| Modelo | Duração | Tempo |
|--------|---------|-------|
| tiny   | 1 min   | 5-10s |
| base   | 1 min   | 8-15s |
| small  | 1 min   | 10-20s |
| medium | 1 min   | 15-30s |
| large  | 1 min   | 20-40s |

### Sem GPU (CPU apenas)

Multiplique os tempos acima por 5-10x.

## 🧪 Testes

### 1. Verificar se português está configurado

```bash
# Testar via API
curl http://localhost:8511/api/health | python -m json.tool

# Verificar logs
docker logs daredevil_web | grep -i português
```

### 2. Testar com arquivo de áudio

```bash
# Se você tem um arquivo MP3 em português
python test_portuguese_br.py

# Ou com curl
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@seu_audio.mp3" \
  -v | python -m json.tool
```

### 3. Comparar com/sem processamento

```python
# No código Python
from transcription.portuguese_processor import PortugueseBRTextProcessor

texto_bruto = "Então tipo você sabe né isso é bem importante hã"
texto_processado = PortugueseBRTextProcessor.process(texto_bruto)

print("Bruto:", texto_bruto)
print("Processado:", texto_processado)
```

## 🌍 Suporte a Outros Idiomas

Você ainda pode transcrever em outros idiomas:

```bash
# Inglês
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=en"

# Espanhol
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=es"

# Francês
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=fr"
```

## 📝 Idiomas Suportados pelo Whisper

- `pt`: Português (Português Brasileiro é padrão)
- `en`: Inglês
- `es`: Espanhol
- `fr`: Francês
- `de`: Alemão
- `it`: Italiano
- `pl`: Polonês
- `ja`: Japonês
- `zh`: Chinês
- E muitos outros...

## 🐛 Troubleshooting

### Texto saindo sem processamento

Verifique se a linguagem é `pt`:

```python
# Logs
logger.info(f"Idioma: {language}")

# Se não for 'pt', o pós-processamento não é aplicado
```

### Hesitações não sendo removidas

- Adicione a hesitação em `PORTUGUESE_BR_CONFIG['hesitations']`
- Reinicie o container

### Abreviações não expandindo

- Verifique a escrita em `PORTUGUESE_BR_CONFIG['abbreviations']`
- Use chaves em minúsculas

## 📚 Recursos Adicionais

- [Documentação Whisper](https://github.com/openai/whisper)
- [Linguagem Portuguesa](https://pt.wikipedia.org/wiki/L%C3%ADngua_portuguesa)
- [Convenções de Escrita em Português](https://www.priberam.pt)

## ✅ Checklist de Implementação

- [x] Português como idioma padrão
- [x] Pós-processamento de texto
- [x] Remoção de hesitações
- [x] Normalização de pontuação
- [x] Expansão de abreviações
- [x] Configuração de ambiente
- [x] Testes de funcionamento
- [x] Documentação completa
- [x] Suporte a GPU
- [x] Exemplos de uso

---

**Última atualização**: 28 de outubro de 2025  
**Versão**: 1.0.0  
**Status**: ✅ Produção
