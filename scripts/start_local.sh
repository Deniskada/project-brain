#!/usr/bin/env bash
set -euo pipefail

# Каталог проекта
cd /home/sa/projects/project-brain

# Переменные окружения (можно задать в .env для постоянства)
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export API_PORT="${API_PORT:-8003}"

echo "Using OLLAMA_HOST=$OLLAMA_HOST"
echo "Using API_PORT=$API_PORT"

# Поднять ChromaDB, Redis и API
docker compose -f docker-compose.local.yml up -d

echo "Waiting for services..."
sleep 5

echo "Check Ollama (host)..."
curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null && echo "Ollama OK" || (echo "Ollama NOT READY"; exit 1)

echo "Check ChromaDB..."
# ChromaDB is mapped as 8002:8000 in docker-compose.local.yml
for i in {1..15}; do
    if curl -fsS http://localhost:8002/api/v1/heartbeat >/dev/null; then
        echo "ChromaDB OK"
        break
    fi
    echo "Waiting for ChromaDB... ($i)"
    sleep 2
done
if ! curl -fsS http://localhost:8002/api/v1/heartbeat >/dev/null; then
    echo "ChromaDB NOT READY"
    docker compose -f docker-compose.local.yml logs chromadb | tail -n 100 || true
    exit 1
fi

echo "Check API..."
for i in {1..15}; do
    if curl -fsS "http://localhost:${API_PORT}/health" >/dev/null; then
        echo "API OK"
        break
    fi
    echo "Waiting for API... ($i)"
    sleep 2
done
if ! curl -fsS "http://localhost:${API_PORT}/health" >/dev/null; then
    echo "API NOT READY"
    docker compose -f docker-compose.local.yml logs api | tail -n 100 || true
    exit 1
fi

echo ""
echo "Open chat:  http://localhost:${API_PORT}"
echo "Health:     http://localhost:${API_PORT}/health"
echo "Index API:  POST http://localhost:${API_PORT}/api/index  {\"project\":\"staffprobot\",\"force_reindex\":true}"