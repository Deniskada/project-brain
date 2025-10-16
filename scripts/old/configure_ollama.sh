#!/bin/bash
# Настройка Ollama для доступа из Docker

echo "Настройка Ollama для прослушивания на всех интерфейсах..."

# Создаем override для systemd
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat << 'EOF' | sudo tee /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

echo "Перезапускаем Ollama..."
sudo systemctl daemon-reload
sudo systemctl restart ollama

echo ""
echo "Проверка..."
sleep 2
curl http://127.0.0.1:11434/api/tags

echo ""
echo ""
echo "✅ Ollama настроен!"
echo "Теперь доступен из Docker на http://172.17.0.1:11434"

