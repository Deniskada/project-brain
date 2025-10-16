# 📚 Руководство по работе с документацией Project Brain

## 🎯 Как получить доступ к документации

### 1. Веб-интерфейс (рекомендуется)

**URL:** `http://localhost:8003/docs`

**Возможности:**
- 🎨 Красивый интерфейс с градиентами
- 🔄 Генерация документации в один клик
- 📊 Статистика проекта (роуты, модели, сервисы)
- 💾 Скачивание в Markdown формате
- 🎯 Три аудитории: разработчики, администраторы, пользователи

**Как использовать:**
1. Откройте браузер: `http://localhost:8003/docs`
2. Выберите проект (по умолчанию: StaffProBot)
3. Выберите аудиторию (разработчики/администраторы/пользователи)
4. Нажмите "Сгенерировать" (генерируется автоматически при загрузке)
5. Скачайте в Markdown (кнопка "Скачать MD")

### 2. API Endpoints

#### Генерация документации
```bash
# Для всех аудиторий
curl -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot"}'

# Для конкретной аудитории
curl -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}'
```

#### Формат ответа
```json
{
  "status": "success",
  "project": "staffprobot",
  "analysis": {
    "routes_count": 466,
    "models_count": 40,
    "services_count": 68,
    "total_files": 3129
  },
  "documentation": {
    "developers": "# 🛠️ Документация для разработчиков...",
    "admins": "# 🔧 Руководство администратора...",
    "users": "# 📖 Руководство пользователя..."
  }
}
```

## 📖 Что включает документация

### Для разработчиков 🛠️
- **API Reference** - полный список эндпоинтов (466 роутов)
- **Database Schema** - все модели БД с полями (40 моделей)
- **Architecture Overview** - структура проекта
- **Services** - список сервисов (68 сервисов)

### Для администраторов 🔧
- **Развертывание** - инструкции по установке
- **Конфигурация** - переменные окружения
- **Мониторинг** - логи, здоровье сервисов
- **Troubleshooting** - частые проблемы

### Для пользователей 📖
- **Введение** - что такое система
- **Быстрый старт** - первые шаги
- **Основные функции** - как работать
- **FAQ** - частые вопросы

## 📊 Текущая статистика (StaffProBot)

- **466 API эндпоинтов** - все роуты FastAPI
- **40 моделей БД** - SQLAlchemy сущности
- **68 сервисов** - бизнес-логика
- **3129 файлов** - весь проект

## 🚀 Примеры использования

### Пример 1: Получить документацию для разработчиков
```bash
curl -s -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}' \
  | jq -r '.documentation.developers' > docs_dev.md
```

### Пример 2: Получить только статистику
```bash
curl -s -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot", "audiences": ["developers"]}' \
  | jq '.analysis'
```

Результат:
```json
{
  "routes_count": 466,
  "models_count": 40,
  "services_count": 68,
  "total_files": 3129
}
```

### Пример 3: Генерация всей документации сразу
```bash
curl -s -X POST http://localhost:8003/api/documentation/generate \
  -H "Content-Type: application/json" \
  -d '{"project": "staffprobot"}' \
  | jq -r '.documentation | to_entries[] | "=== \(.key) ===\n\(.value)\n"' \
  > full_documentation.md
```

## 🔄 Когда документация обновляется

### Сейчас (уже работает):
- ✅ Генерация по требованию через `/docs` или API
- ✅ Всегда актуальная (анализирует текущий код)
- ✅ Быстрая генерация (~5-10 секунд)

### Планируется (Фаза 4.3):
- [ ] Автоматическое обновление при push в GitHub
- [ ] Webhook для триггера регенерации
- [ ] Уведомления в Telegram о готовности
- [ ] Кэширование для ускорения

## 📝 Формат документации

Вся документация генерируется в **Markdown** формате:
- Удобно читать в браузере
- Легко конвертировать в HTML/PDF
- Совместимо с GitHub/GitLab
- Поддержка кода с подсветкой синтаксиса

## 🎨 Кастомизация

### Добавление своего проекта
Отредактируйте `config/projects.yaml`:
```yaml
projects:
  - name: my_project
    path: /path/to/project
    index_patterns:
      - "**/*.py"
      - "**/*.md"
    exclude_patterns:
      - "**/venv/**"
      - "**/__pycache__/**"
```

### Изменение формата документации
Отредактируйте `backend/generators/documentation.py`:
- `generate_for_developers()` - для разработчиков
- `generate_for_admins()` - для админов
- `generate_for_users()` - для пользователей

## 💡 Советы

1. **Первый запуск:** Документация генерируется автоматически при открытии `/docs`
2. **Обновление:** Просто нажмите "Сгенерировать" для актуализации
3. **Экспорт:** Используйте кнопку "Скачать MD" для сохранения
4. **API:** Используйте `/api/documentation/generate` для автоматизации

## 🐛 Troubleshooting

### Документация не генерируется
1. Проверьте, что API запущен: `docker compose -f docker-compose.local.yml ps`
2. Проверьте логи: `docker logs project-brain-api --tail 50`
3. Убедитесь, что путь к проекту правильный в `config/projects.yaml`

### Медленная генерация
- Первая генерация ~10 секунд (анализ проекта)
- Последующие быстрее (кэш анализа)
- Большие проекты (>5000 файлов) могут занять 30+ секунд

### Неполная документация
- Убедитесь, что проект проиндексирован: `curl http://localhost:8003/api/index/status/staffprobot`
- Переиндексируйте: `curl -X POST http://localhost:8003/api/index/staffprobot`

## 📞 Поддержка

- **Веб-интерфейс:** `http://localhost:8003/docs`
- **API документация:** `http://localhost:8003/docs` (FastAPI автодокументация)
- **Статус системы:** `http://localhost:8003/health`

---

**Документация готова к использованию!** 🎉

Просто откройте `http://localhost:8003/docs` в браузере.

