FROM python:3.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg build-essential bash curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar apenas o que precisamos
COPY pyproject.toml /app/

# Instalar UV usando o script oficial do Astral
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Adicionar UV ao PATH
ENV PATH="/root/.local/bin:$PATH"

COPY . /app/

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8511

CMD ["/bin/sh", "-c", "uv sync && python manage.py migrate --noinput && uv run python manage.py runserver 0.0.0.0:8511"]
