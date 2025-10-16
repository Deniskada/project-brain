#!/bin/bash
# Исправление конфигурации Docker для поддержки NVIDIA GPU

echo "=== Настройка Docker для NVIDIA GPU ==="

# Создаем правильную конфигурацию
cat > /tmp/daemon.json << 'EOF'
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF

echo "Копируем конфигурацию..."
sudo cp /tmp/daemon.json /etc/docker/daemon.json

echo "Перезапускаем Docker..."
sudo systemctl daemon-reload
sudo systemctl restart docker

echo ""
echo "Проверка конфигурации..."
docker info | grep -i runtime

echo ""
echo "Тестируем GPU..."
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

echo ""
echo "✅ Готово! Теперь запустите:"
echo "cd /home/sa/projects/project-brain && ./start_ollama_gpu.sh"

