# Project Brain - Быстрый старт

## 🚀 Запуск системы

### 1. Локальное тестирование (без Docker)

```bash
# Переход в директорию проекта
cd /home/sa/projects/project-brain

# Установка зависимостей
pip install -r requirements.txt

# Локальное тестирование компонентов
python test_local.py
```

### 2. Полный запуск с Docker

```bash
# Запуск всех сервисов
docker compose -f docker-compose.local.yml up -d

# Проверка статуса
docker compose -f docker-compose.local.yml ps

# Просмотр логов
docker compose -f docker-compose.local.yml logs ollama
docker compose -f docker-compose.local.yml logs api
```

### 3. Загрузка модели LLM

```bash
# Подключение к контейнеру Ollama
docker compose -f docker-compose.local.yml exec ollama bash

# Загрузка модели (займет время, ~20GB)
ollama pull codellama:34b-instruct-q4_K_M

# Проверка загруженных моделей
ollama list
```

### 4. Индексация проекта StaffProBot

```bash
# Запуск индексации
curl -X POST http://localhost:8001/api/index \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "force_reindex": true}'

# Проверка статуса индексации
curl http://localhost:8001/api/index/status/staffprobot

# Проверка статистики
curl http://localhost:8001/api/stats
```

### 5. Тестирование API

```bash
# Запуск тестов
python scripts/test_api.py

# Или ручное тестирование
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Как работает система отмены смен?", "project": "staffprobot"}'
```

### 6. Веб-интерфейс

Откройте в браузере: http://localhost:8001

## 🔧 Устранение проблем

### Ollama не запускается

```bash
# Проверка логов
docker compose -f docker-compose.local.yml logs ollama

# Перезапуск
docker compose -f docker-compose.local.yml restart ollama
```

### ChromaDB недоступен

```bash
# Проверка логов
docker compose -f docker-compose.local.yml logs chromadb

# Перезапуск
docker compose -f docker-compose.local.yml restart chromadb
```

### API не отвечает

```bash
# Проверка логов
docker compose -f docker-compose.local.yml logs api

# Перезапуск
docker compose -f docker-compose.local.yml restart api
```

### Модель не загружается

```bash
# Проверка доступного места
docker compose -f docker-compose.local.yml exec ollama df -h

# Проверка GPU
docker compose -f docker-compose.local.yml exec ollama nvidia-smi
```

## 📊 Мониторинг

### Проверка статуса всех сервисов

```bash
# Статус контейнеров
docker compose -f docker-compose.local.yml ps

# Использование ресурсов
docker stats

# Логи всех сервисов
docker compose -f docker-compose.local.yml logs -f
```

### Проверка API

```bash
# Health check
curl http://localhost:8001/health

# Статистика
curl http://localhost:8001/api/stats

# Список проектов
curl http://localhost:8001/api/projects
```

## 🎯 Следующие шаги

1. **Индексация StaffProBot** - запустите индексацию для получения знаний о проекте
2. **Тестирование запросов** - попробуйте разные вопросы о коде
3. **Интеграция с Cursor** - используйте API для получения контекста
4. **Настройка правил** - добавьте контекстные правила для разных ролей

## 📚 Документация

- [README.md](README.md) - полная документация
- [API Docs](http://localhost:8001/docs) - Swagger документация
- [Health Check](http://localhost:8001/health) - проверка состояния
