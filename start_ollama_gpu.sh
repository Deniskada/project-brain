#!/bin/bash
# Запуск Ollama с GPU поддержкой

echo "Останавливаем старый контейнер Ollama..."
docker stop project-brain-ollama 2>/dev/null
docker rm project-brain-ollama 2>/dev/null

echo "Создаем volume для данных..."
docker volume create project-brain_ollama_data 2>/dev/null

echo "Запускаем Ollama с GPU..."
docker run -d \
  --name project-brain-ollama \
  --gpus all \
  -p 11434:11434 \
  -v project-brain_ollama_data:/root/.ollama \
  -e OLLAMA_HOST=0.0.0.0 \
  --network project-brain_default \
  --restart unless-stopped \
  ollama/ollama:latest

echo ""
echo "Проверяем GPU..."
sleep 2
docker exec project-brain-ollama nvidia-smi

echo ""
echo "Ollama запущен с GPU!"
echo "Порт: 11434"
echo "Проверить: curl http://localhost:11434/api/tags"

