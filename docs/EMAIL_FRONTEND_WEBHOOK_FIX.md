Subject: 🔧 Erro webhook_url - Solução Rápida

---

Oi,

Encontramos o problema! O erro **"Input should be a valid string"** acontece quando você está enviando `webhook_url` como um objeto vazio ou valor inválido.

**Solução:**

Quando **não quiser usar webhook**, envie de uma destas formas:

❌ **ERRADO:**
```javascript
// NÃO fazer isso:
formData.append('webhook_url', {});     // objeto vazio
formData.append('webhook_url', null);   // null direto
formData.append('webhook_url', undefined); // undefined
```

✅ **CORRETO - Opção 1 (Simples):**
```javascript
// Não incluir webhook_url no FormData:
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('language', 'pt');
// webhook_url não aparece no FormData!

fetch('/api/transcribe/async', { method: 'POST', body: formData });
```

✅ **CORRETO - Opção 2 (Explícito):**
```javascript
// Enviar como string vazia:
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('language', 'pt');
formData.append('webhook_url', '');  // String vazia!

fetch('/api/transcribe/async', { method: 'POST', body: formData });
```

✅ **CORRETO - Opção 3 (Com webhook):**
```javascript
// Se tiver URL de webhook, envie como string:
formData.append('webhook_url', 'https://seu-servidor.com/webhook');
```

---

**RESUMO:**
- Se não quer webhook → **não incluir no FormData** ou enviar **string vazia**
- Se quer webhook → enviar como **URL string válida**
- Nunca enviar `null`, `undefined` ou `{}`

Testa aí que deve resolver! 🚀

Abraços

---
