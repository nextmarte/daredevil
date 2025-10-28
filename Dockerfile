FROM python:3.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg build-essential bash curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar apenas o que precisamos
COPY pyproject.toml /app/

# Instalar UV usando pip
RUN pip install --no-cache-dir uv

# Adicionar UV ao PATH
ENV PATH="/root/.local/bin:$PATH"

COPY . /app/

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore::SyntaxWarning

EXPOSE 8000

CMD ["/bin/sh", "-c", "uv sync && uv run python manage.py migrate --noinput && uv run python manage.py runserver 0.0.0.0:8000"]
