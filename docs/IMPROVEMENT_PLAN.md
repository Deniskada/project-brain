# 🔧 План улучшения точности поиска

## 🎯 Проблема

**Пример:** 
- Вопрос: "Что нужно сделать, чтобы создать объект?"
- AI находит: `domain/entities/object.py` (модель)
- Не находит: `apps/web/routes/objects.py` (роут с формой создания)
- **Результат:** AI не может дать конкретный ответ

## 🔍 Диагностика

### Тест 1: Поиск по роутам
```bash
curl -X POST http://localhost:8003/api/query \
  -d '{"query": "создать объект create object"}' 
```
**Результат:** Находит модель, не находит роут ❌

### Тест 2: Поиск с явным указанием
```bash
curl -X POST http://localhost:8003/api/query \
  -d '{"query": "apps/web/routes/objects.py create_object"}' 
```
**Результат:** Должен найти правильный файл

## 💡 Решения (по приоритету)

### ⚡ Быстрое решение (30 минут) - ДЕЛАЕМ СЕЙЧАС

#### 1. Добавить метаданные типа документа
```python
# backend/indexers/python_indexer.py
metadata = {
    'file': relative_path,
    'type': chunk['type'],
    'doc_type': self._classify_doc_type(relative_path),  # ← ДОБАВИТЬ
    'start_line': chunk.get('start_line', 0),
    'end_line': chunk.get('end_line', 0),
}

def _classify_doc_type(self, file_path: str) -> str:
    """Классификация типа документа"""
    if 'routes' in file_path or 'api' in file_path:
        return 'route'
    elif 'models' in file_path or 'entities' in file_path:
        return 'model'
    elif 'services' in file_path:
        return 'service'
    elif 'handlers' in file_path:
        return 'handler'
    return 'other'
```

#### 2. Улучшить промпт в RAGEngine
```python
# backend/rag/engine.py
async def retrieve_context(self, query: str, ...) -> List[Dict]:
    # Определить тип запроса
    query_type = self._detect_query_type(query)
    
    # Если спрашивают "как сделать" - приоритет роутам
    if query_type == 'how_to':
        where_clause = {"$or": [
            {"doc_type": "route"},
            {"doc_type": "handler"}
        ]}
    
    results = self.collection.query(
        query_embeddings=[query_embedding],
        where=where_clause,  # ← ДОБАВИТЬ фильтр
        n_results=top_k
    )
```

#### 3. Добавить синонимы в промпт
```python
def _build_prompt(self, query: str, context: List[Dict]) -> str:
    # Расширить запрос синонимами
    enriched_query = self._enrich_query(query)
    # "создать объект" → "создать объект, create object, форма создания, роут"
```

### 🚀 Среднее решение (2 часа)

#### 4. Двухэтапный поиск
```python
# 1. Поиск с фильтром по типу
route_results = search(query, doc_type='route')

# 2. Если не нашли - поиск везде
if not route_results:
    all_results = search(query)
```

#### 5. Переранжирование результатов
```python
# После поиска - переранжировать по важности
for result in results:
    # Роуты важнее для вопросов "как"
    if 'как' in query or 'how' in query:
        if result['doc_type'] == 'route':
            result['score'] *= 1.5  # Буст для роутов
```

### 🎯 Долгосрочное решение (1 день)

#### 6. Файн-тюнинг модели эмбеддингов
```python
# Обучить модель на парах (вопрос, правильный файл)
training_data = [
    ("как создать объект", "apps/web/routes/objects.py"),
    ("как открыть смену", "apps/bot/handlers.py"),
    # ... 100+ примеров
]
```

#### 7. Добавить контекстное окно
```python
# Не только функция, но и соседние функции
chunk = {
    'content': function_code,
    'context_before': previous_function,
    'context_after': next_function,
}
```

## 🛠️ План действий (ПРЯМО СЕЙЧАС)

### Шаг 1: Добавить метаданные (10 минут)
- [x] Модифицировать `python_indexer.py`
- [x] Добавить `doc_type` в метаданные
- [x] Классификация по пути файла

### Шаг 2: Улучшить промпт (10 минут)
- [x] Модифицировать `ollama_client.py`
- [x] Добавить контекст типа запроса
- [x] Приоритизация роутов для "как сделать"

### Шаг 3: Переиндексация (10 минут)
- [x] Запустить `/api/index/staffprobot`
- [x] Проверить, что `doc_type` сохраняется
- [x] Тест: вопрос "как создать объект"

### Шаг 4: Проверка (5 минут)
```bash
# До улучшений
curl -X POST http://localhost:8003/api/query \
  -d '{"query": "что нужно сделать, чтобы создать объект?"}'
# Находит: domain/entities/object.py ❌

# После улучшений
# Должен найти: apps/web/routes/objects.py ✅
```

## 📊 Ожидаемые результаты

### До улучшений:
- ❌ Находит модель вместо роута
- ❌ AI не может дать конкретный ответ
- ❌ Пользователь разочарован

### После улучшений:
- ✅ Находит правильный роут
- ✅ AI дает конкретные инструкции
- ✅ Пользователь доволен

## 🎯 Критерии успеха

**Тест 1:** "Что нужно сделать, чтобы создать объект?"
- Должен найти: `apps/web/routes/objects.py`
- Должен показать: форму создания, поля, валидацию

**Тест 2:** "Как открыть смену?"
- Должен найти: `apps/bot/handlers.py` или соответствующий файл
- Должен показать: команды бота, процесс открытия

**Тест 3:** "Какие поля в модели User?"
- Должен найти: `domain/entities/user.py`
- Должен показать: список полей с типами

## 📝 Примечания

- Улучшения **не сломают** существующий функционал
- Можно **откатить** в любой момент
- **30 минут** работы для заметного улучшения
- **ROI высокий** - сразу видны результаты

