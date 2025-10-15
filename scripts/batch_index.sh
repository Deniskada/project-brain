#!/bin/bash
# Пакетная индексация проекта по 20 файлов за раз

API_URL="http://localhost:8003/api"
PROJECT="staffprobot"
BATCH_SIZE=20
TOTAL_ITERATIONS=20  # 20 * 20 = 400 файлов (покроет все 379)

echo "=== Пакетная индексация проекта $PROJECT ==="
echo "Батч: $BATCH_SIZE файлов за итерацию"
echo "Всего итераций: $TOTAL_ITERATIONS"
echo ""

for i in $(seq 1 $TOTAL_ITERATIONS); do
    echo "[$i/$TOTAL_ITERATIONS] Запуск индексации..."
    
    # Запуск индексации
    curl -X POST "$API_URL/index/$PROJECT" -s -o /dev/null -w "HTTP: %{http_code}\n"
    
    # Ждем 10 минут (индексация 20 файлов ~5-7 минут)
    echo "Ожидание завершения (10 минут)..."
    sleep 600
    
    # Проверка статуса
    echo "Проверка статуса..."
    STATUS=$(curl -s "$API_URL/index/status/$PROJECT")
    echo "$STATUS" | python3 -m json.tool
    
    # Пауза между итерациями
    echo "Пауза 30 секунд перед следующей итерацией..."
    sleep 30
    echo ""
done

echo "=== Индексация завершена! ==="
curl -s "$API_URL/index/status/$PROJECT" | python3 -m json.tool

