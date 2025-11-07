# 🚀 GUIA RÁPIDO PARA FRONT-END

## Fluxo de Transcrição Assíncrona

```
CLIENTE                    →    API DAREDEVIL (8511)    →    API REMOTA (192.168.1.29:8591)
                                    ↑                              ↑
                                    |                              |
                              Enfileira task                  Converte áudio
                           (WAV/OGG/MP3/etc)                (16kHz mono)
                                    |
                            Retorna task_id
                                    ↓
                            Client faz polling
```

---

## 1️⃣ Upload de Arquivo

### Request
```bash
curl -X POST \
  -F "file=@audio.ogg" \
  -F "language=pt" \
  -F "webhook_url=http://seu-servidor.com/webhook" \
  http://localhost:8511/api/transcribe/async
```

### Headers Necessários
- `Content-Type: multipart/form-data` (automático)

### Form Fields

| Campo | Tipo | Obrigatório | Exemplo |
|-------|------|-------------|---------|
| `file` | File | ✅ Sim | `audio.ogg` (até 500MB) |
| `language` | String | ✅ Sim | `pt` (português) |
| `webhook_url` | String | ❌ Não | `https://seu-servidor.com/webhook` |

### Response (Sucesso - 200 OK)
```json
{
  "success": true,
  "task_id": "7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d",
  "status_url": "/api/transcribe/async/status/7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d",
  "message": "Transcrição iniciada. Use task_id para consultar o status.",
  "submission_time": 0.18
}
```

### Response (Erro - 422 Unprocessable Entity)
```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["form", "language"],
      "msg": "Input should be a valid string"
    }
  ]
}
```

---

## 2️⃣ Verificar Status (Polling)

### Request
```bash
curl http://localhost:8511/api/transcribe/async/status/7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d
```

### Response - Processando
```json
{
  "task_id": "7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d",
  "state": "STARTED",
  "message": "Transcrição em andamento"
}
```

### Response - Sucesso ✅
```json
{
  "task_id": "7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d",
  "state": "SUCCESS",
  "result": {
    "success": true,
    "transcription": {
      "text": "Olá, como você está?",
      "segments": [
        {
          "start": 0.0,
          "end": 2.5,
          "text": "Olá,",
          "confidence": 0.95
        },
        {
          "start": 2.5,
          "end": 5.0,
          "text": "como você está?",
          "confidence": 0.92
        }
      ],
      "language": "pt",
      "duration": 5.0
    },
    "processing_time": 5.23,
    "audio_info": {
      "format": "ogg",
      "duration": 5.0,
      "sample_rate": 16000,
      "channels": 1,
      "file_size_mb": 0.25
    },
    "error": null,
    "cached": false,
    "task_id": "7ab0c7e8-239a-4461-9bcf-e9731e4e5c3d",
    "total_time": 5.4
  },
  "message": "Transcrição concluída"
}
```

### Response - Erro ❌
```json
{
  "task_id": "15497cc7-7b3e-4792-aabd-964499c6a107",
  "state": "SUCCESS",
  "result": {
    "success": false,
    "transcription": null,
    "error": "Falha na conversão remota de áudio. Verifique: 1) Máquina remota (192.168.1.29) online, 2) API em 192.168.1.29:8591 respondendo, 3) FFmpeg instalado na máquina remota",
    "processing_time": 3.23,
    "audio_info": null,
    "cached": false,
    "task_id": "15497cc7-7b3e-4792-aabd-964499c6a107",
    "total_time": 3.33
  },
  "message": "Transcrição concluída"
}
```

---

## 📊 State Machine

```
              Upload (POST)
                  ↓
            ┌─────────────┐
            │  SUBMITTED  │ ← Imediato (não espera)
            └─────────────┘
                  ↓ (cliente faz polling)
            ┌─────────────┐
            │  STARTED    │ ← Processando (pode levar minutos)
            └─────────────┘
                  ↓
            ┌─────────────┐
            │  SUCCESS    │ ← Final (verificar result.success)
            └─────────────┘
                 / \
               /     \
             TRUE    FALSE
            (✅)      (❌)
```

---

## 🔄 Fluxo Recomendado (JavaScript/TypeScript)

```javascript
// 1. Upload
const formData = new FormData();
formData.append('file', audioFile);
formData.append('language', 'pt');
formData.append('webhook_url', 'https://seu-servidor.com/webhook');

const uploadResponse = await fetch(
  'http://localhost:8511/api/transcribe/async',
  { method: 'POST', body: formData }
);

const { task_id, success } = await uploadResponse.json();

if (!success) {
  console.error('Erro no upload');
  return;
}

console.log('Task criada:', task_id);

// 2. Polling
const pollStatus = async (taskId) => {
  while (true) {
    const statusResponse = await fetch(
      `http://localhost:8511/api/transcribe/async/status/${taskId}`
    );
    
    const data = await statusResponse.json();
    
    if (data.state === 'SUCCESS') {
      // Pronto!
      if (data.result.success) {
        console.log('✅ Transcrição:', data.result.transcription.text);
        return data.result;
      } else {
        console.error('❌ Erro:', data.result.error);
        return null;
      }
    }
    
    // Ainda processando
    console.log('Processando...');
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s
  }
};

const result = await pollStatus(task_id);
```

---

## ✅ Checklist de Integração

- [ ] Formulário coleta arquivo de áudio
- [ ] Formulário coleta idioma (padrão: `pt`)
- [ ] Opcional: Formulário coleta `webhook_url`
- [ ] Upload faz POST para `/api/transcribe/async`
- [ ] Salva `task_id` da resposta
- [ ] Inicia polling a cada 1-2 segundos
- [ ] Verifica `state === 'SUCCESS'`
- [ ] Se `result.success === true`: Mostra transcrição
- [ ] Se `result.success === false`: Mostra `result.error`
- [ ] Webhooks (opcional): Implementa endpoint para receber notificação

---

## 🐛 Troubleshooting

### "Falha na conversão remota"
→ API remota (192.168.1.29:8591) está **offline**  
→ Verifique se máquina remota está ligada  
→ Verifique se FFmpeg está instalado na máquina remota

### "Timeout na conversão"
→ Arquivo muito grande ou máquina remota sobrecarregada  
→ Tente arquivo menor para testar  
→ Verifique CPU/RAM da máquina remota

### "Arquivo vazio"
→ FFmpeg falhou na conversão  
→ Verifique formato do arquivo (OGG, MP3, WAV, etc)  
→ Verifique se arquivo tem faixa de áudio

### "Polling nunca termina"
→ Task travou em estado `STARTED`  
→ Verifique logs do Celery (docker compose logs celery_worker)  
→ Talvez reinicie API

---

## 📈 Performance Esperada

| Formato | Duração | Tempo Total | Status |
|---------|---------|-------------|--------|
| OGG | 30s | ~10s | ⚡ Rápido |
| MP3 | 1min | ~15s | ⚡ Rápido |
| WAV | 5min | ~30s | ✅ OK |
| Vídeo MP4 | 10min | ~60s | 🐢 Lento |

*Tempos com GPU NVIDIA RTX 3060 ativa*

---

## 🔗 Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/transcribe/async` | Upload e criar task |
| `GET` | `/api/transcribe/async/status/{task_id}` | Verificar status |
| `GET` | `/api/health` | Verificar saúde da API |
| `GET` | `/api/gpu-status` | Info da GPU |
| `GET` | `/api/formats` | Formatos suportados |
| `GET` | `/api/docs` | Swagger UI |
| `GET` | `/api/redoc` | ReDoc UI |

---

## 💡 Dicas

1. **Sempre trate os 2 estados de sucesso:**
   - `state === 'SUCCESS'` (task concluiu)
   - `result.success === true` (transcrição funcionou)

2. **Use webhook se possível** (evita polling infinito)

3. **Valide arquivo antes de enviar:**
   - Máximo 500MB
   - Formatos: OGG, MP3, WAV, M4A, FLAC, etc

4. **Use `language=pt` para português** (já é padrão)

5. **Timeout recomendado: 10 minutos** (para arquivos grandes)

---

*Última atualização: 7 de novembro de 2025*  
*Status: ✅ Pronto para Produção*
