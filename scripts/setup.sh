#!/bin/bash

# Project Brain Setup Script

set -e

echo "🚀 Настройка Project Brain..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Проверка GPU (опционально)
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU обнаружен"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
else
    echo "⚠️  NVIDIA GPU не обнаружен, будет использоваться CPU"
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p data logs

# Запуск сервисов
echo "🐳 Запуск Docker сервисов..."
docker compose -f docker-compose.local.yml up -d

# Ожидание запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
echo "📊 Проверка статуса сервисов..."
docker compose -f docker-compose.local.yml ps

# Проверка API
echo "🔍 Проверка API..."
sleep 5
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ API работает"
else
    echo "❌ API недоступен"
    docker compose -f docker-compose.local.yml logs api
    exit 1
fi

# Проверка Ollama
echo "🤖 Проверка Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama работает"
else
    echo "❌ Ollama недоступен"
    docker compose -f docker-compose.local.yml logs ollama
    exit 1
fi

# Проверка ChromaDB
echo "🗄️  Проверка ChromaDB..."
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
    echo "✅ ChromaDB работает"
else
    echo "❌ ChromaDB недоступен"
    docker compose -f docker-compose.local.yml logs chromadb
    exit 1
fi

echo ""
echo "🎉 Project Brain успешно настроен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите модель: docker compose -f docker-compose.local.yml exec ollama ollama pull codellama:34b-instruct-q4_K_M"
echo "2. Запустите индексацию: curl -X POST http://localhost:8001/api/index -H 'Content-Type: application/json' -d '{\"project\": \"staffprobot\"}'"
echo "3. Откройте веб-интерфейс: http://localhost:8001"
echo ""
echo "📚 Документация: README.md"
