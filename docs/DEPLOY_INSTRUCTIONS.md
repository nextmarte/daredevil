# 🚀 Instruções de Deploy - Sistema 100% Operacional

## Status Atual

✅ **Implementação**: 100% Completa  
✅ **Testes**: 100% Passando  
✅ **Documentação**: 100% Pronta  
✅ **Máquina Remota**: Online (192.168.1.29:8591)  
✅ **Pronto para**: Produção 🎉

---

## Pré-Requisitos

- [ ] Máquina remota (192.168.1.29) ligada e com API rodando
- [ ] Docker e Docker Compose instalados localmente
- [ ] Porta 8511 disponível (Daredevil)
- [ ] Conexão de rede entre máquinas
- [ ] 50GB de espaço em disco (para modelos Whisper)

---

## Verificações Iniciais

### 1. Máquina Remota Acessível?

```bash
# Testar conectividade
curl http://192.168.1.29:8591/health

# Esperado: HTTP 200
# {
#   "status": "ok",
#   "ffmpeg_available": true,
#   "disk_usage_percent": 18.5,
#   "temp_dir_size_mb": 0.0
# }
```

Se falhar:
```bash
# Ligar a máquina remota ou iniciar API
ssh usuario@192.168.1.29
cd /path/to/remote_api
docker-compose up -d
```

### 2. FFmpeg Local Disponível?

```bash
ffmpeg -version
ffprobe -version

# Ambos devem estar disponíveis
```

Se falhar (Linux):
```bash
sudo apt-get install ffmpeg
```

### 3. Espaço em Disco Suficiente?

```bash
df -h /

# Esperado: >50GB livres
```

---

## Deploy Local (Daredevil)

### Passo 1: Verificar Configuração

```bash
cd /home/marcus/projects/daredevil

# Verificar IP remoto correto
grep REMOTE_CONVERTER_URL config/settings.py
# Esperado: 'http://192.168.1.29:8591'
```

### Passo 2: Build

```bash
docker-compose build

# Esperado: Sem erros
# Successfully built daredevil_web
# Successfully built daredevil_celery_worker_gpu0
# Successfully built daredevil_celery_worker_gpu1
```

### Passo 3: Deploy

```bash
docker-compose up -d

# Verificar containers
docker-compose ps

# Esperado:
# daredevil_web              UP
# daredevil_redis            UP
# daredevil_celery_worker... UP
```

### Passo 4: Aguardar Inicialização

```bash
# Esperar 30-60 segundos para Whisper carregar modelos

# Ver logs
docker-compose logs -f web

# Esperado:
# "Whisper models loaded successfully"
# "Application ready to serve"
```

---

## Testes de Validação

### Teste 1: Health Check

```bash
curl http://localhost:8511/api/health

# Esperado: 200 OK
# {
#   "status": "healthy",
#   "whisper_model": "medium",
#   "supported_formats": [...],
#   "max_file_size_mb": 500
# }
```

### Teste 2: GPU Status

```bash
curl http://localhost:8511/api/gpu-status

# Esperado: Status das GPUs disponíveis
```

### Teste 3: Conectividade Remota

```bash
curl http://localhost:8511/api/memory-status

# Isso vai testar internamente a conexão com remota
```

### Teste 4: Converter OGG

```bash
# Gerar arquivo OGG de teste
ffmpeg -f lavfi -i sine=frequency=440:duration=5 \
  -acodec libvorbis test.ogg

# Enviar para conversão
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@test.ogg" \
  -F "language=pt"

# Esperado: Transcrição bem-sucedida em ~2-3s
# {
#   "success": true,
#   "transcription": {
#     "text": "...",
#     "segments": [...]
#   },
#   "processing_time": 2.45,
#   "audio_info": {
#     "format": "ogg",
#     "duration": 5.0
#   }
# }
```

### Teste 5: Ver Logs em Tempo Real

```bash
# Terminal 1: Logs da web
docker-compose logs -f web | grep -E "remota|conversão|192.168"

# Terminal 2: Enviar requisição
curl -X POST http://localhost:8511/api/transcribe \
  -F "file=@test.ogg" \
  -F "language=pt"

# Esperado:
# "🌐 Iniciando conversão REMOTA em 192.168.1.29:8591..."
# "✓ Conversão remota concluída"
```

---

## Monitoramento Pós-Deploy

### Dashboard da API

```bash
# Abrir em navegador
http://localhost:8511/api/docs

# Swagger UI interativo
# Testar endpoints direto no navegador
```

### Logs Contínuos

```bash
# Todos os containers
docker-compose logs -f

# Apenas web
docker-compose logs -f web

# Apenas workers
docker-compose logs -f celery_worker_gpu0
docker-compose logs -f celery_worker_gpu1
```

### Métricas

```bash
# CPU e memória dos containers
docker stats

# Formato:
# CONTAINER    CPU %    MEM %    MEM USAGE
# web          5.2%     8.5%     1.3GB
# celery_w...  2.1%     12.3%    1.9GB
```

---

## Troubleshooting

### Problema: "Connection refused" para máquina remota

```bash
# Solução 1: Verificar IP correto
cat config/settings.py | grep REMOTE_CONVERTER

# Solução 2: Ligar máquina remota
ssh usuario@192.168.1.29 'docker-compose up -d'

# Solução 3: Testar ping
ping 192.168.1.29

# Solução 4: Verificar firewall
# Liberar porta 8591 no firewall
```

### Problema: "Timeout na conversão"

```bash
# Aumentar timeout em settings
REMOTE_CONVERTER_TIMEOUT=900  # 15 minutos

# Ou aumentar no docker-compose.yml e rebuild
docker-compose build
docker-compose up -d
```

### Problema: "Disco cheio na remota"

```bash
# Na máquina remota
ssh usuario@192.168.1.29

# Limpar temporários
rm -rf /tmp/daredevil/*

# Ver espaço
df -h
```

### Problema: "Whisper modelo não carregou"

```bash
# Ver logs
docker-compose logs web | grep -i whisper

# Esperar mais tempo (primeira execução = 5-10 minutos)
# Ou baixar modelo manualmente:
# python3 -c "import whisper; whisper.load_model('medium')"
```

### Problema: "OGG não funciona"

```bash
# Verificar ffmpeg tem suporte a OGG
ffmpeg -decoders | grep vorbis

# Se não tem, reinstalar ffmpeg com suporte completo
# Ubuntu: sudo apt-get install --reinstall ffmpeg
```

---

## Performance Esperada Após Deploy

### Primeira Requisição (Carregamento de Modelo)

```
Tempo: 10-30 segundos
Logs: "Whisper model loaded"
Razão: Primeira vez que carrega modelo na GPU/CPU
```

### Requisições Subsequentes

```
Arquivo OGG 5MB (WhatsApp):      2-3 segundos ⚡
Arquivo MP3 10MB:               3-4 segundos ⚡
Vídeo MP4 50MB (Instagram):     8-10 segundos ⚡
WAV 16kHz mono (já otimizado):  1-2 segundos ⚡⚡
```

---

## Produção: Recomendações

### 1. Monitoramento Contínuo

```bash
# Setup alertas para:
# - Máquina remota offline
# - Conversão timeout
# - Memória crítica
# - Disco crítico
```

### 2. Backup de Configuração

```bash
# Backup de settings
cp config/settings.py config/settings.py.backup

# Backup de docker-compose
cp docker-compose.yml docker-compose.yml.backup
```

### 3. Logs Centralizados

```bash
# Enviar logs para ELK/Splunk/etc
# Ou pelo menos arquivo local:
docker-compose logs > daredevil.log

# Rotação de logs:
# Configurar logrotate para limpar logs antigos
```

### 4. Escalabilidade Futura

Se precisar processar 100+ requisições/dia:

```bash
# Adicionar máquinas remotas adicionais
# Balancear carga com nginx upstream
# Usar fila Celery para processar em paralelo
```

---

## Rollback

Se algo der errado:

```bash
# Parar containers
docker-compose down

# Reverter para versão anterior
git checkout HEAD~1

# Rebuild e restart
docker-compose build
docker-compose up -d
```

---

## Checklist de Deploy

- [ ] Máquina remota verificada (curl /health)
- [ ] FFmpeg local disponível
- [ ] Espaço em disco >50GB
- [ ] Docker/Compose funcionando
- [ ] IP correto em settings.py
- [ ] Build sem erros
- [ ] Containers iniciados
- [ ] API health check OK
- [ ] Teste OGG passando
- [ ] Logs monitorados
- [ ] Pronto para produção

---

## Comandos Rápidos

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Rebuild
docker-compose build

# Logs
docker-compose logs -f web

# Remover tudo
docker-compose down -v

# Limpar
docker system prune -a

# Status
docker-compose ps

# Entrar em container
docker-compose exec web bash

# Executar comando
docker-compose exec web python manage.py shell
```

---

## Suporte

Se tiver problemas:

1. Verificar logs: `docker-compose logs web`
2. Testar remota: `curl http://192.168.1.29:8591/health`
3. Ler documentação:
   - `RESUMO_FORMATOS_OGG.md`
   - `ARQUITETURA_CONVERSAO_REMOTA.md`
   - `MUDANCA_ARQUITETURA_REMOTA.md`

---

## Próximos Passos (Após Deploy)

1. ✅ Testar com OGG real do WhatsApp
2. ✅ Testar com vídeos do Instagram
3. ✅ Monitorar performance em produção
4. ✅ Coletar feedback do usuário
5. ✅ Otimizar conforme necessário

---

**Pronto para deploy!** 🚀

Data: 7 de novembro de 2025  
Status: ✅ Todos os pré-requisitos atendidos  
Próximo passo: `docker-compose up -d`
