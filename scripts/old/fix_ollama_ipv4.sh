#!/bin/bash
# Настройка Ollama для IPv4

echo "Настройка Ollama для IPv4..."

# Обновляем конфигурацию
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

echo "Перезапускаем Ollama..."
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo ""
echo "Ждем запуска..."
sleep 3

echo ""
echo "Проверка IPv4:"
curl http://172.17.0.1:11434/api/tags | head -1

echo ""
echo ""
echo "✅ Готово!"

