# Использование Project Brain

## 1. Запуск окружения
```bash
cd /home/sa/projects/project-brain

# Первичная настройка переменных
cp env.example .env  # если файла ещё нет

# Запуск сервисов
docker compose -f docker-compose.local.yml up -d

# Проверка
docker compose -f docker-compose.local.yml ps
curl http://localhost:8003/health
```

## 2. Индексация проектов
```bash
# StaffProBot
curl -X POST http://localhost:8003/api/index/staffprobot

# Project Brain (опционально)
curl -X POST http://localhost:8003/api/index/project-brain

# Проверка статуса
curl http://localhost:8003/api/index/status/staffprobot
curl http://localhost:8003/api/index/status/project-brain
```

## 3. Работа с AI
```bash
# Через API
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "как создать объект?", "project": "staffprobot"}'

# Через веб-интерфейс
http://localhost:8003/chat
```

## 4. Генерация документации
```bash
# Разработчики
curl -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}'

# Экспорт
curl -X POST http://localhost:8003/api/documentation/export/markdown \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot"}' > docs_staffprobot.md
```

Веб-интерфейс документации: `http://localhost:8003/docs` (генерация при загрузке, поддержка скачивания MD).

## 5. Автообновление через GitHub
```bash
# Ручной триггер (аналог webhook)
curl -X POST http://localhost:8003/api/webhook/manual-reindex/staffprobot

# Статусы
curl http://localhost:8003/api/webhook/status
curl http://localhost:8003/api/webhook/status/staffprobot
```
Подробности — в `GITHUB_AUTO_UPDATE_GUIDE.md`.

## 6. Мониторинг и обслуживание
```bash
# Логи
docker compose -f docker-compose.local.yml logs api -f

# Логи ChromaDB/Redis
docker compose -f docker-compose.local.yml logs chromadb -f
docker compose -f docker-compose.local.yml logs redis -f

# Перезапуск API
docker compose -f docker-compose.local.yml restart api
```

## 7. Типовые вопросы
```bash
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "где хранится логика открытия смен?", "project": "staffprobot"}'

curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "какие есть роли в системе?", "project": "staffprobot"}'
```

## 8. Очистка и повторный запуск
```bash
# Аккуратная остановка
docker compose -f docker-compose.local.yml down

# Полная очистка (вместе с volume)
docker compose -f docker-compose.local.yml down -v

docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d
```

