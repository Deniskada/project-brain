#!/bin/bash
# Полный перезапуск Docker с nvidia runtime

echo "Остановка всех контейнеров..."
docker stop $(docker ps -aq) 2>/dev/null

echo "Остановка Docker..."
sudo systemctl stop docker
sudo systemctl stop docker.socket

echo "Очистка Docker процессов..."
sudo pkill dockerd 2>/dev/null
sleep 2

echo "Запуск Docker..."
sudo systemctl start docker

echo "Проверка статуса..."
sudo systemctl status docker --no-pager | head -15

echo ""
echo "Проверка nvidia runtime..."
docker run --rm --runtime=nvidia nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

echo ""
echo "Готово! Теперь запустите:"
echo "cd /home/sa/projects/project-brain && docker compose -f docker-compose.local.yml up -d"

