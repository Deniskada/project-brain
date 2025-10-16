#!/bin/bash
# Принудительный перезапуск Docker

echo "Останавливаем все контейнеры..."
docker stop $(docker ps -aq) 2>/dev/null

echo "Останавливаем Docker полностью..."
sudo systemctl stop docker
sudo systemctl stop docker.socket
sudo systemctl stop containerd

echo "Убиваем все процессы Docker..."
sudo pkill -9 dockerd 2>/dev/null
sudo pkill -9 containerd 2>/dev/null
sleep 3

echo "Перезагружаем systemd..."
sudo systemctl daemon-reload

echo "Запускаем containerd..."
sudo systemctl start containerd
sleep 2

echo "Запускаем Docker..."
sudo systemctl start docker
sleep 3

echo ""
echo "Проверка конфигурации..."
docker info | grep -A 3 -i runtime

echo ""
echo "Если видите 'Default Runtime: nvidia' - все готово!"

