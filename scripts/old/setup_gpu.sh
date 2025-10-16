#!/bin/bash
# Скрипт для настройки NVIDIA Container Toolkit и GPU в Docker

echo "=== Установка NVIDIA Container Toolkit ==="

# 1. Добавление репозитория
echo "Шаг 1: Добавление репозитория..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Обновление и установка
echo "Шаг 2: Установка пакетов..."
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Настройка Docker
echo "Шаг 3: Настройка Docker..."
sudo nvidia-ctk runtime configure --runtime=docker

# 4. Перезапуск Docker
echo "Шаг 4: Перезапуск Docker..."
sudo systemctl restart docker

echo "=== Установка завершена! ==="
echo ""
echo "Теперь запустите Docker Compose с GPU:"
echo "cd /home/sa/projects/project-brain"
echo "docker compose -f docker-compose.local.yml down"
echo "docker compose -f docker-compose.local.yml up -d"

