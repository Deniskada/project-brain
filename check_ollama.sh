#!/bin/bash
# Проверка доступности Ollama

echo "=== Проверка Ollama ==="

echo ""
echo "1. Статус сервиса:"
sudo systemctl status ollama --no-pager | head -10

echo ""
echo "2. Порты Ollama:"
sudo netstat -tulpn | grep 11434

echo ""
echo "3. Тест с localhost:"
curl http://localhost:11434/api/tags

echo ""
echo "4. Тест с 127.0.0.1:"
curl http://127.0.0.1:11434/api/tags

echo ""
echo "5. Тест с 0.0.0.0:"
curl http://0.0.0.0:11434/api/tags

