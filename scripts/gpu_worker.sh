#!/bin/bash
# Script para iniciar worker Celery com GPU específica

GPU_ID=${1:-0}
WORKER_NAME="worker_gpu${GPU_ID}"

# Definir CUDA_VISIBLE_DEVICES ANTES de rodar Python
export CUDA_VISIBLE_DEVICES=$GPU_ID

echo "🔷 Iniciando $WORKER_NAME com GPU $GPU_ID"
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

# Executar worker com uv run
exec uv run celery -A config worker \
  --loglevel=info \
  --concurrency=1 \
  -n $WORKER_NAME@%h
