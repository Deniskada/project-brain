#!/usr/bin/env python3
"""
Обучающий скрипт: добавление пар вопрос-ответ в базу знаний
Используется для fine-tuning RAG на специфических данных проекта
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, '/app')

from backend.rag.engine import RAGEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обучающие пары вопрос-ответ для StaffProBot
QA_PAIRS = [
    {
        "question": "Какие роли пользователей есть в системе StaffProBot?",
        "answer": """В системе StaffProBot существует 5 ролей пользователей:

1. **owner** (владелец) - полный доступ ко всем функциям:
   - Управление компанией и всеми объектами
   - Создание и управление сотрудниками
   - Назначение менеджеров
   - Просмотр всех отчётов и аналитики
   
2. **manager** (управляющий) - управление назначенными объектами:
   - Управление сотрудниками на своих объектах
   - Создание графиков смен
   - Просмотр отчётов по своим объектам
   
3. **employee** (сотрудник) - базовый функционал:
   - Открытие и закрытие смен
   - Просмотр своего графика
   - Отправка геолокации
   
4. **admin** (администратор) - техническое управление системой
   
5. **moderator** (модератор) - управление контентом и отзывами

Роли определены в файле domain/entities/user.py через enum UserRole.""",
        "metadata": {
            "file": "domain/entities/user.py",
            "category": "architecture",
            "difficulty": "easy"
        }
    },
    {
        "question": "Как происходит открытие смены сотрудником?",
        "answer": """Процесс открытия смены сотрудником:

1. **Инициация**: Сотрудник нажимает кнопку "Открыть смену" в Telegram боте
2. **Геолокация**: Система запрашивает текущее местоположение
3. **Проверка расстояния**: 
   - Вычисляется расстояние до объекта работы
   - Проверка через calculate_distance() из core/geolocation/
   - Допустимое расстояние: MAX_DISTANCE метров
4. **Проверка активных смен**: Проверяется, нет ли уже открытой смены
5. **Создание записи**: 
   - Создается запись Shift в БД
   - start_time = текущее время
   - status = "active"
   - coordinates = местоположение сотрудника
6. **Уведомление**: Сотрудник получает подтверждение

Код обработки находится в:
- apps/bot/handlers/shift_handlers.py - обработчик команды
- shared/services/shift_service.py - бизнес-логика
- domain/entities/shift.py - модель данных""",
        "metadata": {
            "file": "shared/services/shift_service.py",
            "category": "business_logic",
            "difficulty": "medium"
        }
    },
    {
        "question": "В чём разница между telegram_id и user_id в StaffProBot?",
        "answer": """КРИТИЧЕСКИ ВАЖНО понимать разницу:

**telegram_id**:
- Уникальный ID пользователя Telegram (integer)
- Присваивается Telegram при регистрации
- Используется для аутентификации через бот
- Сохраняется в поле User.telegram_id
- Получается из update.from_user.id

**user_id**:
- Внутренний ID записи в базе данных (auto-increment primary key)
- Генерируется PostgreSQL при создании пользователя
- Используется для внутренних связей (ForeignKey)
- Сохраняется в поле User.id
- НЕ совпадает с telegram_id!

**ПРАВИЛО**: Для работы с БД ВСЕГДА используй user_id, НЕ telegram_id!

**Как правильно получить user_id**:
```python
from shared.services.user_service import get_user_id_from_current_user

# В веб-роуте
user_id = await get_user_id_from_current_user(current_user, session)

# Теперь можно использовать
shift = await shift_repo.get_by_user(user_id)
```

Подробнее: doc/user_id_handling.mdc""",
        "metadata": {
            "file": "doc/user_id_handling.mdc",
            "category": "authentication",
            "difficulty": "hard"
        }
    },
    {
        "question": "Где находится модель User и какие поля она содержит?",
        "answer": """Модель User находится в файле: **domain/entities/user.py**

Основные поля модели:
- **id** (Integer) - внутренний ID в БД (PRIMARY KEY)
- **telegram_id** (BigInteger) - ID пользователя в Telegram (UNIQUE)
- **username** (String) - username в Telegram
- **first_name** (String) - имя
- **last_name** (String) - фамилия  
- **phone** (String) - телефон
- **role** (Enum: UserRole) - роль: owner/manager/employee/admin/moderator
- **is_active** (Boolean) - активен ли пользователь
- **created_at** (DateTime) - дата регистрации
- **updated_at** (DateTime) - дата последнего обновления

Связи:
- **shifts** - список смен (relationship to Shift)
- **contracts** - список договоров (relationship to Contract)
- **managed_objects** - объекты под управлением (для manager)

Используется SQLAlchemy ORM с async/await.""",
        "metadata": {
            "file": "domain/entities/user.py",
            "category": "database",
            "difficulty": "easy"
        }
    },
    {
        "question": "Какие API endpoints есть для работы с объектами?",
        "answer": """API endpoints для работы с объектами (Objects):

**Для владельца (Owner):**
- GET `/owner/objects` - список всех объектов
- POST `/owner/objects/create` - создание объекта
- GET `/owner/objects/{id}` - детали объекта
- POST `/owner/objects/{id}/update` - обновление объекта
- POST `/owner/objects/{id}/delete` - удаление объекта
- GET `/owner/objects/{id}/employees` - сотрудники объекта

**Для управляющего (Manager):**
- GET `/manager/objects` - список назначенных объектов
- GET `/manager/objects/{id}` - детали объекта (только назначенные)
- GET `/manager/objects/{id}/employees` - сотрудники объекта

**Для сотрудника (Employee):**
- GET `/employee/objects` - список объектов, где работает

Роуты находятся в:
- apps/web/routes/owner/objects.py
- apps/web/routes/manager/objects.py  
- apps/web/routes/employee/objects.py""",
        "metadata": {
            "file": "apps/web/routes/owner/objects.py",
            "category": "api",
            "difficulty": "medium"
        }
    },
    {
        "question": "Как работает система календаря смен?",
        "answer": """Система календаря смен в StaffProBot:

**Архитектура:**
- Shared Calendar API - routes/shared/calendar_api.py
- НЕ дублируется для каждой роли
- Универсальный API для всех ролей

**API Endpoints:**
- GET `/api/calendar/shifts` - получение смен за период
  - Параметры: start_date, end_date, object_id, user_id
  - Фильтрация по правам доступа
  
- POST `/api/calendar/shift/create` - создание смены
- PUT `/api/calendar/shift/{id}/update` - обновление
- DELETE `/api/calendar/shift/{id}/delete` - удаление

**Frontend:**
- JavaScript календарь: static/js/shared/universal_calendar.js
- CSS стили: static/css/shared/calendar.css
- Используется FullCalendar.js
- Поддержка drag-and-drop для управляющих

**Права доступа:**
- Owner: видит все смены всех объектов
- Manager: только свои объекты
- Employee: только свои смены

Документация: doc/vision_v1/shared/calendar.md""",
        "metadata": {
            "file": "routes/shared/calendar_api.py",
            "category": "features",
            "difficulty": "medium"
        }
    },
    {
        "question": "Как развернуть StaffProBot на production?",
        "answer": """Развёртывание StaffProBot на production:

**1. Подготовка сервера:**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**2. Клонирование проекта:**
```bash
cd /opt
git clone https://github.com/Deniskada/staffprobot.git
cd staffprobot
```

**3. Конфигурация:**
```bash
# Копирование .env
cp env.example .env
nano .env  # Заполнить production значения

# Переменные для прода:
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://redis:6379
SECRET_KEY=<сгенерировать>
TELEGRAM_BOT_TOKEN=<от BotFather>
```

**4. Запуск:**
```bash
# Production режим
docker compose -f docker-compose.prod.yml up -d

# Проверка статуса
docker compose -f docker-compose.prod.yml ps

# Логи
docker compose -f docker-compose.prod.yml logs -f web
```

**5. Nginx (если нужен):**
- Конфиг: deployment/nginx/staffprobot.conf
- SSL через Let's Encrypt

**6. Мониторинг:**
- Health check: https://staffprobot.ru/health
- Prometheus metrics: /metrics

Подробная документация: deployment/README.md""",
        "metadata": {
            "file": "deployment/README.md",
            "category": "deployment",
            "difficulty": "hard"
        }
    },
    {
        "question": "Что делать если возникает ошибка при создании договора с активным договором?",
        "answer": """Ошибка "У пользователя уже есть активный договор":

**Причина:**
Система не позволяет создавать более одного активного договора для одного сотрудника.

**Решение:**
1. Проверить активные договоры:
```python
active_contracts = await contract_repo.get_active_by_user(user_id, session)
```

2. Закрыть старый договор перед созданием нового:
```python
# Установить end_date для старого
old_contract.end_date = datetime.now()
old_contract.is_active = False
await session.commit()
```

3. Или использовать функцию автозакрытия:
```python
from shared.services.contract_service import close_previous_contracts
await close_previous_contracts(user_id, session)
```

**Обработка в коде:**
apps/web/services/contract_service.py - проверка перед созданием

**Исправление:**
commit 19ea8ea: добавлена проверка активных договоров с понятным сообщением об ошибке

Файл: apps/web/routes/employees.py - обработчик создания договора""",
        "metadata": {
            "file": "apps/web/services/contract_service.py",
            "category": "troubleshooting",
            "difficulty": "medium"
        }
    }
]

async def train_qa_pairs(project: str = "staffprobot"):
    """Добавление обучающих пар в базу знаний"""
    logger.info(f"🎓 Начало обучения: {project}")
    logger.info(f"📚 Пар вопрос-ответ: {len(QA_PAIRS)}")
    
    # Инициализация RAG
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    for i, pair in enumerate(QA_PAIRS, 1):
        logger.info(f"\n[{i}/{len(QA_PAIRS)}] Добавление: {pair['question'][:60]}...")
        
        # Создаём обучающий документ
        training_doc = f"""
ВОПРОС: {pair['question']}

ОТВЕТ: {pair['answer']}

---
Категория: {pair['metadata'].get('category', 'general')}
Сложность: {pair['metadata'].get('difficulty', 'medium')}
Файл: {pair['metadata'].get('file', 'N/A')}
"""
        
        # Добавляем в базу знаний
        await rag_engine.store_document(
            project=project,
            content=training_doc,
            metadata={
                'file': pair['metadata'].get('file', 'training_qa'),
                'type': 'qa_pair',
                'doc_type': 'training',
                'question': pair['question'],
                'category': pair['metadata'].get('category'),
                'difficulty': pair['metadata'].get('difficulty'),
                'project': project
            }
        )
        
        logger.info(f"  ✅ Добавлено")
    
    logger.info(f"\n✅ Обучение завершено! Добавлено {len(QA_PAIRS)} пар")

async def verify_training(project: str = "staffprobot"):
    """Проверка качества обучения"""
    logger.info(f"\n🧪 Проверка обучения...")
    
    rag_engine = RAGEngine()
    await rag_engine.initialize()
    
    # Тестовые вопросы
    test_questions = [
        "Какие роли в StaffProBot?",
        "Как открыть смену?",
        "Разница telegram_id и user_id?"
    ]
    
    for question in test_questions:
        logger.info(f"\n❓ {question}")
        result = await rag_engine.query(
            project=project,
            query=question,
            top_k=3
        )
        
        if result and result.get('sources'):
            logger.info(f"  ✅ Найдено источников: {len(result['sources'])}")
            logger.info(f"  📝 Превью: {result['answer'][:100]}...")
        else:
            logger.info(f"  ⚠️ Источники не найдены")

if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "staffprobot"
    
    asyncio.run(train_qa_pairs(project))
    asyncio.run(verify_training(project))

