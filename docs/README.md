# Project Brain — Обзор

## Назначение
Project Brain — локальная система управления знаниями для проектов StaffProBot. Платформа индексирует код и документацию, сохраняет их в ChromaDB и отвечает на запросы через RAG-движок с локальной LLM. Основные сценарии: быстрый поиск контекста разработчиками, генерация актуальной документации и автоматическое обновление базы знаний после изменений в репозитории.

## Текущее состояние (09.11.2025)
- RAG-движок (ChromaDB + `qwen2.5:14b-instruct`) обслуживает проект `staffprobot`; коллекция `kb_staffprobot` содержит 720 документов.
- Генератор документации доступен по `http://localhost:8003/docs` и через API `/api/documentation/generate`.
- Автообновление через GitHub webhook готово: `/api/webhook/github`, статус `/api/webhook/status/{project}`.
- Health и статусы работают: `/health`, `/api/stats`, `/api/stats/staffprobot`, `/api/index/status/staffprobot`.
- Последние исправления (09.11.2025): переход на `chromadb.HttpClient`, обновлённые эндпоинты статуса индексации, стабилизированная переиндексация.

## Быстрый старт
1. Запустить окружение: `docker compose -f docker-compose.local.yml up -d`.
2. Проверить здоровье: `curl http://localhost:8003/health`.
3. Открыть чат: `http://localhost:8003/chat` (по умолчанию выбран проект `staffprobot`).
4. При необходимости запустить индексацию: `curl -X POST http://localhost:8003/api/index/staffprobot`.

## Структура документации
- `STATUS.md` — актуальный прогресс по фазам и ключевые метрики.
- `USAGE.md` — запуск, индексация, ответы на частые операции.
- `DOCUMENTATION_GUIDE.md` — как генерируется документация и где её получить.
- `GITHUB_AUTO_UPDATE_GUIDE.md` — настройка автоиндексации через GitHub webhook.
- `ROADMAP.md` — ближайшие приоритеты (Фазы 5–6).
- `archive/` — исторические отчёты и черновики.

## Полезные команды
```bash
# Статусы
curl http://localhost:8003/api/stats
curl http://localhost:8003/api/stats/staffprobot
curl http://localhost:8003/api/index/status/staffprobot

# Индексация
curl -X POST http://localhost:8003/api/index/staffprobot
curl -X POST http://localhost:8003/api/webhook/manual-reindex/staffprobot

# Документация
curl -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}'
```
