FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

# Instalar Python 3.12 e dependências
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    bash \
    curl \
    ca-certificates \
    software-properties-common \
    tzdata \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
  && rm -rf /var/lib/apt/lists/*

# Criar symlink para python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 \
  && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

WORKDIR /app

# Instalar UV usando o script oficial do Astral
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Adicionar UV ao PATH permanentemente
ENV PATH="/root/.local/bin:$PATH"

# Copiar arquivos do projeto
COPY pyproject.toml uv.lock* /app/
COPY . /app/

# Tornar o entrypoint executável
RUN chmod +x /app/docker-entrypoint.sh

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Usar o entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
