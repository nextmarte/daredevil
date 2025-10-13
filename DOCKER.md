# 🐳 Docker Setup - Daredevil API

API de transcrição rodando em container Docker na porta **8511**.

## 🚀 Quick Start

### Opção 1: Build Local com UV (Recomendado)

O build local usa `python:3.12-slim` (glibc) que é compatível com wheels de pacotes como `torch` e `openai-whisper`.

```bash
# Build da imagem
docker compose build web

# Subir o container
docker compose up -d

# Ver logs
docker compose logs -f web
```

### Opção 2: Imagem UV do GitHub (Alpine)

Usa a imagem oficial do UV, mas pode ter problemas com pacotes que precisam de wheels manylinux (como torch).

```bash
# Subir usando a imagem UV do GHCR
UV_IMAGE=ghcr.io/astral-sh/uv:0.9.2-python3.14-alpine docker compose up -d

# Ver logs
docker compose logs -f web
```

## 📦 Como funciona o `uv sync`

O projeto usa **UV** como gerenciador de dependências. O processo de instalação acontece automaticamente:

1. **No entrypoint** (`docker-entrypoint.sh`):
   - Instala ffmpeg (necessário para processamento de áudio)
   - Executa `uv sync` para instalar todas as dependências do `pyproject.toml`
   - Cria/atualiza o ambiente virtual `.venv`
   - Aplica migrações do Django
   - Inicia o servidor na porta 8511

2. **Fluxo de instalação**:
   ```bash
   uv sync                          # Lê pyproject.toml e uv.lock
   ↓
   Cria .venv/                      # Ambiente virtual isolado
   ↓
   Instala todas as dependências    # Django, Whisper, pydub, etc.
   ↓
   uv run python manage.py ...      # Executa comandos no ambiente
   ```

## 🔧 Comandos Úteis

### Gerenciar Container

```bash
# Parar container
docker compose down

# Rebuild completo (força reconstrução)
docker compose build --no-cache web

# Restart
docker compose restart web

# Ver status
docker compose ps
```

### Acessar Shell no Container

```bash
# Entrar no container
docker exec -it daredevil_web /bin/bash

# Dentro do container você pode:
uv sync                                    # Reinstalar dependências
uv run python manage.py migrate           # Rodar migrações
uv run python manage.py shell             # Django shell
uv run python manage.py createsuperuser   # Criar usuário admin
```

### Ver Logs

```bash
# Logs em tempo real
docker compose logs -f web

# Últimas 100 linhas
docker logs --tail 100 daredevil_web

# Logs de erro
docker compose logs web | grep -i error
```

## 🌐 Testando a API

Após subir o container, a API estará disponível em `http://localhost:8511`

```bash
# Testar health check
curl http://localhost:8511/api/health

# Testar transcrição (exemplo)
curl -X POST "http://localhost:8511/api/transcribe" \
  -F "file=@seu_audio.opus" \
  -F "language=pt"
```

## ⚙️ Variáveis de Ambiente

Configure no `docker-compose.yml` ou crie um arquivo `.env`:

```bash
DEBUG=1                              # Debug mode (0 ou 1)
WHISPER_MODEL=medium                 # Modelo Whisper (base, small, medium, large)
MAX_AUDIO_SIZE_MB=25                 # Tamanho máximo do arquivo
TEMP_AUDIO_DIR=/tmp/daredevil        # Diretório temporário
ALLOWED_HOSTS=*                      # Hosts permitidos (usar domínios em produção)
PYTHONUNBUFFERED=1                   # Logs sem buffer
```

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs completos
docker compose logs web

# Verificar se a porta 8511 está em uso
lsof -i :8511
# ou
netstat -tuln | grep 8511
```

### Erro de instalação de dependências (torch/whisper)

**Problema**: Em Alpine (musl), pacotes como `torch` não têm wheels compatíveis.

**Solução**: Use o build local (Opção 1) que usa glibc:
```bash
docker compose build web
docker compose up -d
```

### Forçar reinstalação de dependências

```bash
# Remover .venv do container e recriar
docker compose down
docker compose up -d --force-recreate
```

### Limpar volumes e caches

```bash
# Parar e remover tudo
docker compose down -v

# Remover imagens antigas
docker image prune -a
```

## 📁 Estrutura de Arquivos Docker

```
daredevil/
├── Dockerfile                    # Imagem base com Python 3.12 + ffmpeg
├── docker-compose.yml            # Orquestração do container
├── docker-entrypoint.sh          # Script de inicialização (uv sync + runserver)
├── .dockerignore                 # Arquivos ignorados no build
└── pyproject.toml                # Dependências gerenciadas pelo UV
    └── [tool.uv]                 # Configurações do UV
```

## 🔐 Produção

Para ambiente de produção, considere:

1. **Usar Gunicorn** em vez de `runserver`:
   ```bash
   uv run gunicorn config.wsgi:application --bind 0.0.0.0:8511
   ```

2. **Configurar ALLOWED_HOSTS** adequadamente:
   ```bash
   ALLOWED_HOSTS=seu-dominio.com,api.seu-dominio.com
   ```

3. **Usar volumes para persistência**:
   ```yaml
   volumes:
     - ./media:/app/media        # Upload de arquivos
     - db_data:/app/db           # Banco de dados
   ```

4. **Adicionar healthcheck**:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8511/api/health"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

## 📚 Links Úteis

- [UV Documentation](https://github.com/astral-sh/uv)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

**Porta exposta**: 8511  
**Comando de execução**: `uv run python manage.py runserver 0.0.0.0:8511`  
**Dependências instaladas via**: `uv sync` (automático no entrypoint)
