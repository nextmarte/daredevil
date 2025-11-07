# 🔧 SOLUÇÃO - Expor Porta 8591 em Ultron

## Problema Encontrado

A API de conversão está rodando em ultron, mas **NÃO está exposta** no host:

```
converter-app | * Running on http://127.0.0.1:8591
converter-app | * Running on http://172.27.0.3:8591  ← Apenas rede Docker interna!
```

**Resultado:** Daredevil não consegue conectar (`[Errno 113] No route to host`)

## Solução Rápida

### Em ultron, adicionar ao docker-compose.yml:

```yaml
services:
  converter-app:
    ports:
      - "8591:8591"  # ← ADICIONAR ESTA LINHA!
```

### Redeployar:

```bash
docker compose down
docker compose up -d
```

### Testar:

```bash
# De qualquer máquina na rede:
curl http://192.168.1.29:8591/health
```

**Isso vai expor a porta 8591 do container no host ultron! 🎉**
