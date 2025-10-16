#!/bin/bash
# Установка Ollama на хост (не в Docker) для использования GPU

echo "=== Установка Ollama на хост ==="

# Установка Ollama
echo "Загружаем и устанавливаем Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo ""
echo "Проверяем установку..."
which ollama

echo ""
echo "Запускаем Ollama как сервис..."
sudo systemctl enable ollama
sudo systemctl start ollama

echo ""
echo "Проверяем статус..."
sudo systemctl status ollama --no-pager | head -10

echo ""
echo "Проверяем доступность API..."
sleep 2
curl http://localhost:11434/api/tags

echo ""
echo ""
echo "✅ Ollama установлен и запущен на хосте с GPU!"
echo ""
echo "Теперь загрузите модель:"
echo "ollama pull codellama:13b-instruct"
echo ""
echo "И обновите docker-compose, чтобы API подключался к http://host.docker.internal:11434"

