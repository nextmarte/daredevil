# Setup Local - Daredevil API

## Dependências do Sistema

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### Verificar instalação
```bash
ffmpeg -version
ffprobe -version
```

## Instalação Python (com uv)

```bash
# Instalar dependências
uv sync

# Aplicar migrações
uv run python manage.py migrate

# Executar servidor
uv run python manage.py runserver
```

## Docker (Recomendado)

```bash
# Build e executar
docker compose up --build

# Verificar health
curl http://localhost:8511/api/health
```
