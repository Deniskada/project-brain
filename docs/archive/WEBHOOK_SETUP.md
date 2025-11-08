# Настройка GitHub Webhook для автообновления

## 🎯 Что делает webhook?

При каждом `git push` в `main/master`:
1. **Получает уведомление** от GitHub
2. **Обновляет код** (`git pull`) на сервере
3. **Переиндексирует** весь проект в ChromaDB
4. **База знаний актуализируется** автоматически

## 📋 Требования

### 1. Проект должен быть в `config/projects.yaml`:

```yaml
projects:
  - name: staffprobot
    path: /projects/staffprobot  # ← путь на сервере
    git_url: https://github.com/Deniskada/staffprobot  # ← URL репозитория
    index_patterns:
      - "**/*.py"
      - "**/*.md"
    exclude_patterns:
      - "**/venv/**"
      - "**/__pycache__/**"
```

**Важно:**
- `path` - абсолютный путь к проекту на сервере
- `git_url` - URL GitHub репозитория
- Проект должен быть **git-репозиторием** с настроенным `origin`

### 2. Git настроен на сервере:

```bash
# Проверка
cd /projects/staffprobot
git remote -v  # должен показать origin

# Настройка (если нужно)
git remote add origin https://github.com/Deniskada/staffprobot.git
git fetch origin
git branch --set-upstream-to=origin/main main
```

### 3. Права доступа:

```bash
# Контейнер должен иметь доступ к .git
docker compose -f docker-compose.local.yml exec api ls -la /projects/staffprobot/.git

# Если нет доступа - проверить volumes в docker-compose
```

## 🔧 Настройка в GitHub

### 1. Открыть настройки репозитория:

```
GitHub → Repository → Settings → Webhooks → Add webhook
```

### 2. Заполнить форму:

| Поле | Значение |
|------|----------|
| **Payload URL** | `https://your-domain.com/api/webhook/github` |
| **Content type** | `application/json` |
| **Secret** | `your_secret_key` (опционально, но рекомендуется) | 63f4945d921d599f27ae4fdf5bada3f1
| **Events** | Just the push event |
| **Active** | ✅ Enabled |

### 3. Создать `.env` файл с секретом:

```bash
# Копируем шаблон
cp env.example .env

# Генерируем уникальный секрет
openssl rand -hex 32

# Добавляем в .env
echo "GITHUB_WEBHOOK_SECRET=<ваш_сгенерированный_секрет>" >> .env
```

Или вручную отредактируйте `.env`:
```bash
# В файле .env
GITHUB_WEBHOOK_SECRET=63f4945d921d599f27ae4fdf5bada3f1
```

### 4. Перезапустить контейнеры:

```bash
# Чтобы подхватить новые переменные окружения
docker compose -f docker-compose.local.yml restart api

# Проверить, что секрет загрузился
docker compose -f docker-compose.local.yml exec api printenv | grep GITHUB_WEBHOOK_SECRET
```

**Примечание:** Проверка подписи включена по умолчанию в `backend/api/routes/webhook.py`. Если секрет не задан в `.env`, проверка пропускается.

## 🧪 Тестирование

### 1. Проверка endpoint:

```bash
curl http://localhost:8003/api/webhook/test
# {"status":"ok","message":"Webhook API работает!"}
```

### 2. Ручной запуск переиндексации:

```bash
curl -X POST http://localhost:8003/api/webhook/manual-reindex/staffprobot
# {"status":"accepted","message":"Reindexing staffprobot started in background"}
```

### 3. Проверка логов:

```bash
docker compose -f docker-compose.local.yml logs api -f | grep -E "GitHub Push|git pull|Индексация"
```

### 4. Тестовый коммит:

```bash
cd /path/to/your/repo
echo "test" > test.txt
git add test.txt
git commit -m "Test webhook"
git push origin main

# Смотрим логи Docker
docker logs project-brain-api -f
```

Ожидаемый вывод:
```
🔄 GitHub Push: staffprobot, ref: refs/heads/main, commits: 1
🚀 Запуск переиндексации для staffprobot
📥 Обновление кода: git pull в /projects/staffprobot
✅ Код обновлён: Already up to date. (или список изменений)
📚 Начинаем индексацию проекта: staffprobot
...
✅ Индексация завершена: {'total_files': X, 'total_chunks': Y, 'errors': 0}
```

## 🚨 Troubleshooting

### Проблема: "Git операция timeout"

**Причина:** `git pull` занимает > 60 секунд

**Решение:**
```python
# В webhook.py увеличить timeout:
timeout=120  # вместо 60
```

### Проблема: "git pull failed: Permission denied"

**Причина:** Контейнер не имеет доступа к `.git` или SSH ключам

**Решение 1 (HTTPS):**
```bash
# Используйте HTTPS вместо SSH
cd /projects/staffprobot
git remote set-url origin https://github.com/Deniskada/staffprobot.git
```

**Решение 2 (SSH):**
```yaml
# В docker-compose.local.yml добавить:
volumes:
  - ~/.ssh:/root/.ssh:ro  # монтируем SSH ключи
```

### Проблема: "Конфигурация проекта не найдена"

**Причина:** Имя репозитория не совпадает с `project_map` в webhook

**Решение:**
```python
# В webhook.py обновить project_map:
project_map = {
    'staffprobot': 'staffprobot',
    'your-repo-name': 'your-project-name'  # ← добавить
}
```

### Проблема: "Already up to date" но индексация не запускается

**Причина:** Локальная копия уже актуальна (например, на dev-машине)

**Решение:** Это нормально! Индексация всё равно запустится и обновит базу знаний.

## 📊 Мониторинг

### Просмотр истории webhook в GitHub:

```
Repository → Settings → Webhooks → Recent Deliveries
```

Показывает:
- ✅ Успешные запросы (200)
- ❌ Ошибки (4xx, 5xx)
- 📋 Payload и Response

### Логи Project Brain:

```bash
# Все webhook события
docker logs project-brain-api 2>&1 | grep "GitHub Push"

# Только ошибки
docker logs project-brain-api 2>&1 | grep "ERROR.*webhook"
```

## 🔐 Безопасность

### ⚠️ БЕЗ секрета (только для dev):
Любой может отправить POST на webhook и запустить переиндексацию

### ✅ С секретом (для production):
GitHub подписывает каждый запрос HMAC-SHA256, webhook проверяет подпись

**Настройка:**
```bash
# 1. Сгенерировать секрет
openssl rand -hex 32

# 2. Добавить в .env
echo "GITHUB_WEBHOOK_SECRET=<ваш_секрет>" >> .env

# 3. Перезапустить контейнер
docker compose -f docker-compose.prod.yml restart api
```

## 📝 Дополнительные возможности

### Webhook для нескольких проектов:

```yaml
# config/projects.yaml
projects:
  - name: staffprobot
    path: /projects/staffprobot
    git_url: https://github.com/Deniskada/staffprobot
  
  - name: project-brain
    path: /app
    git_url: https://github.com/your-org/project-brain
```

### Webhook только для определённых файлов:

```python
# В webhook.py добавить проверку:
commits = payload.get('commits', [])
changed_files = []
for commit in commits:
    changed_files.extend(commit.get('added', []))
    changed_files.extend(commit.get('modified', []))

# Переиндексировать только если изменились .py или .md
if any(f.endswith(('.py', '.md')) for f in changed_files):
    # индексация
```

## 🎉 Готово!

Теперь при каждом `git push`:
1. ✅ Код обновляется автоматически
2. ✅ База знаний переиндексируется
3. ✅ RAG отвечает с актуальной информацией

**Проверка работы:**
```bash
# 1. Сделать изменение в коде
# 2. git push
# 3. Подождать 1-2 минуты
# 4. Задать вопрос через API
curl -X POST http://localhost:8003/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "расскажи о новых изменениях"}'
```

