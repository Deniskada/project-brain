# Project Brain

Система управления знаниями проекта на базе локальной LLM с RAG для памяти Cursor, генерации документации и поддержки пользователей.

## Архитектура

- **Backend:** FastAPI + LangChain + ChromaDB
- **LLM:** Ollama + GPU (16GB VRAM)
- **Индексация:** AST парсинг Python, Markdown
- **Frontend:** HTML/JS чат-интерфейс

## 📚 Документация

- **[Настройка GitHub Webhook](WEBHOOK_SETUP.md)** - автообновление кода при коммитах
- **[Улучшения RAG](IMPROVEMENTS_SUMMARY.md)** - детали качественных улучшений
- **[Статус проекта](doc/project-status.md)** - прогресс разработки

## Быстрый старт

### Локальная разработка (inference server)

```bash
# Клонирование и переход в директорию
cd /home/sa/projects/project-brain

# Запуск всех сервисов
docker compose -f docker-compose.local.yml up -d

# Проверка статуса
docker compose -f docker-compose.local.yml ps

# Просмотр логов
docker compose -f docker-compose.local.yml logs ollama
docker compose -f docker-compose.local.yml logs api
```

### Загрузка модели

```bash
# Подключение к контейнеру Ollama
docker compose -f docker-compose.local.yml exec ollama bash

# Загрузка модели (займет время)
ollama pull codellama:34b-instruct-q4_K_M

# Проверка загруженных моделей
ollama list
```

### Индексация проекта

```bash
# Запуск индексации StaffProBot
curl -X POST http://localhost:8001/api/index \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "force_reindex": true}'

# Проверка статуса
curl http://localhost:8001/api/index/status/staffprobot
```

### Тестирование

```bash
# Тест API
curl http://localhost:8001/health

# Тест запроса
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Как работает система отмены смен?", "project": "staffprobot"}'
```

## API Endpoints

- `GET /` - Веб-интерфейс
- `GET /health` - Проверка здоровья
- `POST /api/query` - Запрос к AI
- `POST /api/index` - Индексация проекта
- `GET /api/projects` - Список проектов
- `GET /api/stats` - Статистика
- `GET /api/context-rules` - Контекстные правила для Cursor

## Конфигурация

Проекты настраиваются в `config/projects.yaml`:

```yaml
projects:
  - name: staffprobot
    path: /projects/staffprobot
    index_patterns:
      - "**/*.py"
      - "**/*.md"
    exclude_patterns:
      - "**/venv/**"
      - "**/__pycache__/**"
```

## Интеграция с Cursor

### REST API

```bash
# Получение контекста для файла
curl "http://localhost:8001/api/context-rules?file=apps/web/routes/owner.py&role=owner"

# Запрос к AI
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Как работает система отмены смен?", "context": {"file": "apps/web/routes/cancellations.py"}}'
```

## Производство

### На сервере (клиент)

```bash
# Обновление IP в docker-compose.prod.yml
# Запуск клиента
docker compose -f docker-compose.prod.yml up -d
```

## Требования

- **Локальная машина:** 16GB VRAM, 32GB RAM, 100GB SSD
- **Сервер:** 2GB RAM, 10GB SSD (только клиент)
- **Docker:** с поддержкой GPU (nvidia-docker)

## Модели

- **Основная:** `codellama:34b-instruct-q4_K_M` (20GB)
- **Fallback:** `codellama:13b-instruct` (7GB)

## Разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск в режиме разработки
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8001
```
