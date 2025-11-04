#!/bin/bash
# Полная индексация StaffProBot с мониторингом

set -e

PROJECT="staffprobot"
LOG_FILE="/tmp/reindex_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "🚀 Полная индексация: $PROJECT"
echo "📅 $(date)"
echo "📝 Лог: $LOG_FILE"
echo "=========================================="
echo

# Проверка контейнера
if ! docker ps | grep -q project-brain-api; then
    echo "❌ Контейнер project-brain-api не запущен!"
    exit 1
fi

echo "✅ Контейнер запущен"
echo "🔄 Запуск индексации..."
echo

# Запуск индексации с выводом в лог и терминал
docker compose -f /home/sa/projects/project-brain/docker-compose.local.yml exec -T api \
    python /app/scripts/simple_reindex.py $PROJECT 2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Индексация завершена успешно!"
else
    echo "❌ Ошибка индексации (код: $EXIT_CODE)"
fi
echo "📝 Полный лог: $LOG_FILE"
echo "=========================================="

exit $EXIT_CODE

