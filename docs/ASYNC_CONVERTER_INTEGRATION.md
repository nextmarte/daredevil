# 📧 Email de Integração - Serviço de Conversão de Áudio Remoto

---

**Assunto:** Novo Endpoint Assíncrono - Serviço de Conversão de Áudio Remoto | Migração Obrigatória

---

## Olá,

Finalizado o desenvolvimento do **Serviço de Conversão de Áudio em Máquina Remota** para o Daredevil. 

O serviço agora suporta **conversões assíncronas** que permitem processar **múltiplas requisições em paralelo** sem bloquear o Daredevil. Isto é crítico para melhorar a responsividade da API.

---

## 📋 Mudança Importante

### ❌ **Endpoint Antigo (Síncrono)**
```
POST http://192.168.1.29:8591/convert
```
**Problema:** Bloqueia a requisição até terminar a conversão (pode levar segundos)

### ✅ **Novo Endpoint (Assíncrono - RECOMENDADO)**
```
POST http://192.168.1.29:8591/convert-async
GET http://192.168.1.29:8591/convert-status/<job_id>
GET http://192.168.1.29:8591/convert-download/<job_id>
```
**Vantagem:** Retorna imediatamente com `job_id`, libera o Daredevil, você acompanha depois

---

## 🔄 Fluxo de Integração (3 passos)

### **Passo 1: Enviar para Fila**
```python
import requests

# Enviar arquivo para conversão
response = requests.post(
    "http://192.168.1.29:8591/convert-async",
    files={"file": open("audio.wav", "rb")}
)

job_id = response.json()["job_id"]
print(f"✅ Conversão enfileirada: {job_id}")
```

**Resposta (HTTP 202 - Aceito):**
```json
{
  "job_id": "9bfe3086-40d2-42aa-8a83-2711cbccf138",
  "status": "queued",
  "status_url": "/convert-status/9bfe3086-40d2-42aa-8a83-2711cbccf138",
  "download_url": "/convert-download/9bfe3086-40d2-42aa-8a83-2711cbccf138"
}
```

---

### **Passo 2: Acompanhar Progresso** (opcional, mas recomendado)
```python
import time

# Acompanhar status
max_attempts = 60  # Máx 1 minuto
attempts = 0

while attempts < max_attempts:
    status_response = requests.get(
        f"http://192.168.1.29:8591/convert-status/{job_id}"
    )
    data = status_response.json()
    
    print(f"Status: {data['status']} ({data.get('progress', 0)}%)")
    
    if data["status"] == "completed":
        print("✅ Conversão concluída!")
        break
    elif data["status"] == "failed":
        print(f"❌ Erro: {data.get('error')}")
        break
    
    time.sleep(0.5)  # Verificar a cada 500ms
    attempts += 1

if attempts >= max_attempts:
    print("⏱️ Timeout - conversão demorando muito")
```

**Estados Possíveis:**

| Estado | Progresso | Descrição |
|--------|-----------|-----------|
| `pending` | 0% | Aguardando na fila |
| `processing` | 0-100% | Convertendo |
| `completed` | 100% | Pronto para download |
| `failed` | - | Erro na conversão |

**Exemplo de Resposta:**
```json
{
  "job_id": "9bfe3086-40d2-42aa-8a83-2711cbccf138",
  "status": "processing",
  "progress": 75,
  "message": "Convertendo com FFmpeg..."
}
```

---

### **Passo 3: Baixar Arquivo**
```python
# Baixar arquivo convertido
download_response = requests.get(
    f"http://192.168.1.29:8591/convert-download/{job_id}"
)

# Salvar como WAV 16kHz mono
with open("output.wav", "wb") as f:
    f.write(download_response.content)

print("✅ Arquivo salvo!")
```

---

## 📝 Exemplo Completo (Copy & Paste)

```python
import requests
import time

def converter_audio_assincrono(caminho_arquivo):
    """Converte áudio para WAV 16kHz mono de forma assíncrona."""
    
    # 1. Enviar para fila
    print(f"📤 Enviando {caminho_arquivo}...")
    response = requests.post(
        "http://192.168.1.29:8591/convert-async",
        files={"file": open(caminho_arquivo, "rb")}
    )
    
    if response.status_code != 202:
        print(f"❌ Erro: {response.text}")
        return None
    
    job_id = response.json()["job_id"]
    print(f"✅ Job {job_id} enfileirado\n")
    
    # 2. Acompanhar conversão
    print("⏳ Aguardando conversão...")
    while True:
        status_response = requests.get(
            f"http://192.168.1.29:8591/convert-status/{job_id}"
        )
        data = status_response.json()
        
        if data["status"] == "completed":
            print(f"✅ Conversão concluída! ({data.get('size_mb', 0):.2f}MB)\n")
            break
        elif data["status"] == "failed":
            print(f"❌ Erro: {data.get('error')}")
            return None
        else:
            progress = data.get("progress", 0)
            print(f"  {progress}% {data.get('message', '')}", end="\r")
        
        time.sleep(0.5)
    
    # 3. Baixar arquivo
    print("📥 Baixando arquivo...")
    download_response = requests.get(
        f"http://192.168.1.29:8591/convert-download/{job_id}"
    )
    
    output_path = caminho_arquivo.replace(
        caminho_arquivo.split(".")[-1], 
        "wav"
    )
    
    with open(output_path, "wb") as f:
        f.write(download_response.content)
    
    print(f"✅ Arquivo salvo em: {output_path}")
    return output_path


# USO:
if __name__ == "__main__":
    resultado = converter_audio_assincrono("whatsapp_audio.ogg")
```

---

## 🎯 Parâmetros Opcionais

Se precisar de configurações customizadas:

```python
requests.post(
    "http://192.168.1.29:8591/convert-async",
    files={"file": open("audio.mp3", "rb")},
    data={
        "sample_rate": 16000,  # Padrão: 16000 (ideal para Whisper)
        "channels": 1          # Padrão: 1 (mono)
    }
)
```

---

## 🛡️ Proteções Implementadas

O serviço foi configurado para **não sobrecarregar** a máquina:

| Parâmetro | Valor | Proteção |
|-----------|-------|----------|
| **Workers simultâneos** | 4 | Máx 4 conversões rodando |
| **FFmpeg threads** | 16 | Máx 16 cores por conversão |
| **Timeout** | 30 min | Arquivo descartado se muito lento |
| **Tamanho max** | 1000 MB | Não aceita arquivos muito grandes |

---

## 📊 Monitorar Fila em Tempo Real

Para ver o status da fila e conversões ativas:

```bash
curl http://192.168.1.29:8591/status | jq
```

**Resposta:**
```json
{
  "active_conversions": 2,          # Rodando agora
  "queued_conversions": 5,          # Esperando na fila
  "completed_today": 142,
  "failed_today": 1,
  "avg_conversion_time_seconds": 0.89,
  "temp_dir_size_mb": 542.34,
  "max_concurrent_workers": 4,
  "ffmpeg_threads_limit": 16
}
```

---

## ⚙️ Configuração no Daredevil

### Cliente Integrado (Já Existe)
Se usar a classe `RemoteAudioConverter` do arquivo `client_example.py`:

```python
from daredevil_client import RemoteAudioConverter

converter = RemoteAudioConverter(base_url="http://192.168.1.29:8591")

# Versão síncrona (compatibilidade)
wav_data = converter.convert_to_wav("audio.mp3")

# Versão assíncrona (nova - recomendada)
job_id = converter.convert_to_wav_async("audio.mp3")
status = converter.get_status(job_id)
wav_data = converter.download(job_id)
```

### Integração Manual
Se preferir fazer direto no seu código:

```python
import requests

# Configuração
CONVERTER_URL = "http://192.168.1.29:8591"

# Enviar
response = requests.post(
    f"{CONVERTER_URL}/convert-async",
    files={"file": open("audio.wav", "rb")}
)

if response.status_code == 202:
    job_id = response.json()["job_id"]
    print(f"Job enfileirado: {job_id}")
else:
    print(f"Erro: {response.text}")
```

---

## ✅ Checklist de Integração

- [ ] Ler documentação completa em: `QUEUE_CONFIGURATION.md`
- [ ] Testar endpoint `/convert-async` com arquivo pequeno
- [ ] Testar `/convert-status/<job_id>` para acompanhar
- [ ] Implementar `/convert-download/<job_id>` no Daredevil
- [ ] Substituir chamadas para `/convert` por `/convert-async`
- [ ] Adicionar tratamento de erro para `status == "failed"`
- [ ] Testar com múltiplas requisições simultâneas
- [ ] Monitorar `/status` durante testes

---

## 🚨 Troubleshooting

### "Conversão muito lenta"
→ Verificar: `curl http://192.168.1.29:8591/status | jq .active_conversions`  
→ Se 4/4, fila está saturada  
→ Tentar novamente em alguns segundos

### "Arquivo inválido"
→ Formato não suportado por FFmpeg  
→ Verificar resposta de erro: `status == "failed"`  
→ Converter para MP3 ou WAV antes

### "Job não encontrado"
→ Job expirou (dados deletados após 6 horas)  
→ Enviar arquivo novamente

---

## 📞 Suporte

- **IP/Porta:** 192.168.1.29:8591
- **Health check:** `GET http://192.168.1.29:8591/health`
- **Documentação completa:** `QUEUE_CONFIGURATION.md`
- **Exemplos código:** `client_example.py` + `daredevil_client.py`

---

## 📈 Performance Esperada

Com base em testes:

| Arquivo | Tamanho | Tempo | Realtime |
|---------|---------|-------|----------|
| WhatsApp OGG | 228 KB | 253 ms | 402x faster |
| MP4 (11min) | 43 MB | 1.0 s | 787x faster |
| Typical MP3 | ~5 MB | 100-300 ms | 1000x+ faster |

**Conclusão:** Conversão em fração de segundo, ideal para streaming de requisições

---

## 🎁 Bônus: Script de Teste

```bash
#!/bin/bash

CONVERTER="http://192.168.1.29:8591"
FILE="test_audio.wav"

echo "1️⃣  Enviando para fila..."
RESPONSE=$(curl -s -X POST -F "file=@$FILE" $CONVERTER/convert-async)
JOB_ID=$(echo $RESPONSE | jq -r .job_id)
echo "✅ Job ID: $JOB_ID"

echo -e "\n2️⃣  Acompanhando progresso..."
while true; do
    STATUS=$(curl -s $CONVERTER/convert-status/$JOB_ID | jq -r .status)
    PROGRESS=$(curl -s $CONVERTER/convert-status/$JOB_ID | jq -r .progress)
    
    echo "Status: $STATUS ($PROGRESS%)"
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Pronto!"
        break
    fi
    
    sleep 1
done

echo -e "\n3️⃣  Baixando arquivo..."
curl -s $CONVERTER/convert-download/$JOB_ID --output output.wav
echo "✅ Arquivo salvo em output.wav"
```

---

## 🔗 Endpoints Completos

### `POST /convert-async` - Enviar para Fila
```
Requisição:
  - Method: POST
  - Content-Type: multipart/form-data
  - Body: file (binary), sample_rate (int, opcional), channels (int, opcional)

Resposta (HTTP 202):
  {
    "job_id": "uuid",
    "status": "queued",
    "status_url": "/convert-status/<job_id>",
    "download_url": "/convert-download/<job_id>"
  }
```

### `GET /convert-status/<job_id>` - Acompanhar
```
Requisição:
  - Method: GET
  - URL: /convert-status/{job_id}

Resposta (HTTP 200):
  {
    "job_id": "uuid",
    "status": "processing|completed|failed|pending",
    "progress": 0-100,
    "message": "string",
    "size_mb": 1.23,
    "error": "string (se falhou)"
  }
```

### `GET /convert-download/<job_id>` - Baixar
```
Requisição:
  - Method: GET
  - URL: /convert-download/{job_id}

Resposta (HTTP 200):
  - Content-Type: audio/wav
  - Body: WAV file (binary)
```

### `GET /health` - Health Check
```
Requisição:
  - Method: GET
  - URL: /health

Resposta (HTTP 200):
  {
    "status": "ok",
    "ffmpeg_available": true,
    "disk_usage_percent": 18.5,
    "temp_dir_size_mb": 0.0
  }
```

### `GET /status` - Monitorar Fila
```
Requisição:
  - Method: GET
  - URL: /status

Resposta (HTTP 200):
  {
    "active_conversions": 2,
    "queued_conversions": 5,
    "completed_today": 142,
    "failed_today": 1,
    "avg_conversion_time_seconds": 0.89,
    "temp_dir_size_mb": 542.34,
    "max_concurrent_workers": 4,
    "ffmpeg_threads_limit": 16
  }
```

---

## 🚀 Próximos Passos

1. ✅ Ler esta documentação
2. ✅ Testar endpoints com cURL
3. ✅ Integrar RemoteAudioConverter no Daredevil
4. ✅ Implementar retry automático
5. ✅ Adicionar monitoramento de fila
6. ✅ Deploy em produção

---

**Qualquer dúvida, me avisa! 🚀**

---

*Mensagem gerada: 07/11/2025*  
*Serviço: Remote Audio Converter v1.1 (Assíncrono)*  
*Localização: http://192.168.1.29:8591*
