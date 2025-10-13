Uso Docker (resumo)

1) Rodar com a imagem oficial UV (puxa ghcr):

```bash
UV_IMAGE=ghcr.io/astral-sh/uv:0.9.2-python3.14-alpine docker compose up -d
```

2) Se preferir build local (recomendado quando o projeto precisa de pacotes com wheels manylinux como torch):

```bash
docker compose build web
docker compose up -d
```

Notas importantes:
- O entrypoint roda `uv sync` automaticamente para instalar dependências a partir do `pyproject.toml`.
- Em Alpine (musl) alguns pacotes como `torch` podem não ter wheel compatível; nesse caso use a imagem baseada em glibc (build local usando `Dockerfile`) ou ajuste `UV_IMAGE` para uma imagem glibc do UV.
- O servidor expõe a porta 8511 (mapeada por docker-compose).
