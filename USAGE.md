# Использование Project Brain

## 🚀 Запуск

```bash
cd /home/sa/projects/project-brain

# Создать .env из шаблона (первый раз)
cp env.example .env

# Запустить все сервисы
docker compose -f docker-compose.local.yml up -d

# Проверить статус
docker compose -f docker-compose.local.yml ps
```

## 📚 Индексация проектов

### Проиндексировать StaffProBot:
```bash
curl -X POST http://localhost:8003/api/index/staffprobot
```

### Проиндексировать Project Brain:
```bash
curl -X POST http://localhost:8003/api/index/project-brain
```

### Проверить статус:
```bash
curl http://localhost:8003/api/index/status/staffprobot
curl http://localhost:8003/api/index/status/project-brain
```

## 💬 Задать вопрос AI

### Через curl:
```bash
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "как создать объект в StaffProBot?",
    "project": "staffprobot"
  }'
```

### Через веб-интерфейс:
```
http://localhost:8003/chat
```

## 🔄 GitHub Webhook (автообновление)

### Настройка в GitHub:
1. **Repository → Settings → Webhooks → Add webhook**
2. **Payload URL:** `https://your-domain.com/api/webhook/github`
3. **Content type:** `application/json`
4. **Secret:** Скопировать из `.env` → `GITHUB_WEBHOOK_SECRET`
5. **Events:** Just the push event

### Ручной запуск переиндексации:
```bash
curl -X POST http://localhost:8003/api/webhook/manual-reindex/staffprobot
```

## 📄 Генерация документации

### Для разработчиков:
```bash
curl -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project": "staffprobot",
    "audiences": ["developers"]
  }'
```

### Экспорт в HTML:
```bash
curl -X POST http://localhost:8003/api/documentation/export/html \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}' \
  > docs.html
```

### Экспорт в Markdown:
```bash
curl -X POST http://localhost:8003/api/documentation/export/markdown \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot"}' \
  > docs.md
```

## 🔧 Добавление нового проекта

### 1. Добавить в `config/projects.yaml`:
```yaml
projects:
  - name: my-project
    path: /path/to/project
    git_url: https://github.com/user/my-project
    index_patterns:
      - "**/*.py"
      - "**/*.md"
    exclude_patterns:
      - "**/venv/**"
      - "**/__pycache__/**"
    description: "Описание проекта"
```

### 2. Монтировать в Docker:
```yaml
# docker-compose.local.yml
volumes:
  - /path/to/project:/path/to/project:ro
```

### 3. Проиндексировать:
```bash
docker compose -f docker-compose.local.yml restart api
curl -X POST http://localhost:8003/api/index/my-project
```

## 📊 Мониторинг

### Просмотр логов:
```bash
docker compose -f docker-compose.local.yml logs api -f
```

### Проверка здоровья:
```bash
curl http://localhost:8003/health
```

### Статистика индексации:
```bash
curl http://localhost:8003/api/stats
```

## 🛑 Остановка

```bash
docker compose -f docker-compose.local.yml down
```

## 🔥 Полная очистка и перезапуск

```bash
# Остановить и удалить всё (включая volumes)
docker compose -f docker-compose.local.yml down -v

# Удалить образы
docker compose -f docker-compose.local.yml down --rmi all

# Пересобрать и запустить
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d

# Переиндексировать проекты
curl -X POST http://localhost:8003/api/index/staffprobot
curl -X POST http://localhost:8003/api/index/project-brain
```

## 💡 Типичные вопросы

### "Как создать X?"
```bash
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "как создать объект?", "project": "staffprobot"}'
```
→ RAG найдёт роуты и покажет конкретный код

### "Какие поля у модели Y?"
```bash
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "какие поля у модели User?", "project": "staffprobot"}'
```
→ RAG найдёт модель БД и покажет структуру

### "Какие API endpoints для Z?"
```bash
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "какие API endpoints для объектов?", "project": "staffprobot"}'
```
→ RAG найдёт роуты и API документацию

## 🎯 Production деплой

См. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) для полной инструкции.

Кратко:
1. Скопировать `env.example` → `.env` и установить production значения
2. Использовать `docker-compose.prod.yml`
3. Настроить Nginx reverse proxy
4. Добавить SSL сертификат (Let's Encrypt)
5. Настроить GitHub webhook
6. Настроить бэкапы ChromaDB

## 📖 Дополнительная документация

- [WEBHOOK_SETUP.md](WEBHOOK_SETUP.md) - настройка GitHub webhook
- [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md) - улучшения RAG
- [doc/project-status.md](doc/project-status.md) - статус разработки

