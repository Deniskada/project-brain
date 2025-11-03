# Project Brain — Roadmap

> Цель: сделать Project Brain активным участником DevOps-цикла StaffProBot: анализ архитектуры (AST), хранение знаний (ChromaDB), обучение на событиях (коммиты/бады/FAQ), визуализация связей и иерархий, API для бота и веба.

## Прогресс по итерациям

| Итерация | Название | Статус | Прогресс |
|---|---|---|---|
| 1 | AST‑парсер, классификация, веса, сохранение в ChromaDB+Redis | Завершена | 100% |
| 2 | API: reindex/analyze/graph/node/meta/weights/tasks‑sync/diagram/diff | Завершена | 100% |
| 3 | SPA (React + D3/Vis.js): дерево/граф/фильтры/панель узла | В работе | 35% |
| 4 | Интеграция с DevOps Dashboard (webhook) | В работе | 70% |
| 5 | Загрузка FAQ/bugs/changelog/commits в RAG + FAQ AI API | В работе | 80% |
| 6 | CI/CD: main‑deploy‑and‑train.yml | Завершена | 100% |
| 7 | (Опц.) Neo4j‑адаптер и экспорт/синхронизация | Запланировано | 0% |

## Источники знаний (синхронизировано с documentation_rules)

- Код: `/projects/staffprobot/**` (apps/, core/, domain/, shared/)
- Документация: `staffprobot/doc/**`, `staffprobot/doc/vision_v1/**`, `staffprobot/docs/**`
- DevOps артефакты: `staffprobot/doc/DEVOPS_COMMAND_CENTER.md`, `.github/workflows/**`
- Roadmap/итерации: `staffprobot/doc/plans/**`, `roadmap.md`, аналитические отчёты `ANALYSIS_*.md`, `TEST_REPORT_*.md`
- База знаний пользователей (через API StaffProBot или прямой доступ в dev): таблицы `faq_entries`, `bug_logs`, `changelog_entries`
- Коммиты: `git log` и/или GitHub API
- Правила/конвенции: `doc/DOCUMENTATION_RULES.md`, `doc/user_id_handling.mdc`, `vision.md`, `workflow.mdc`, `migrations.mdc`

## Архитектура хранения

- ChromaDB (PRIMARY):
  - RAG-документы (код/доки/FAQ/баги/changelog/коммиты)
  - Архитектурные коллекции: `arch_nodes`, `arch_edges`, `arch_snapshots`, `arch_diffs` (богатые метаданные: type, role, subsystem, file, lines, fqn, degree, weight)
- Redis (CACHE):
  - Последняя сборка графа (JSON) для быстрого фронтенда
  - Статусы задач, очереди, debounce вебхуков
- Neo4j (OPTIONAL):
  - Включается флагом (для сложных граф‑запросов); синхронизация из Chroma/AST результата

## Потоки

1) Обучение с нуля
- AST‑парсинг → функции/классы/эндпойнты/вызовы (с разрешением импортов)
- Классификация роль/подсистема по путям + эвристики
- Построение графа (узлы/рёбра), расчёт весов: `role*0.4 + subsystem*0.3 + degree_norm*0.3`
- Сохранение: ChromaDB (архив + элементы), Redis (агрегированный JSON), снапшот JSON
- Загрузка RAG: FAQ/bugs/changelog/commits в отдельные коллекции

2) Инкрементальные обновления (GitHub Actions + Webhook)
- `POST /api/architecture/analyze` с `commit_sha`
- Diff (узлы/рёбра) + Mermaid диаграмма
- Обновление Chroma коллекций и Redis-графа
- Webhook → StaffProBot `/api/admin/devops/brain/update`

## Интеграция с DevOps Command Center

- После `analyze`/`reindex` отправлять сводку: `total_nodes`, `total_edges`, `changed_nodes`, `changed_edges`, `processing_time`, ссылки на `diagram.mmd` и `latest.json`.
- Отражать на дашборде (см. `staffprobot/doc/DEVOPS_COMMAND_CENTER.md`).

## Эндпоинты

- `POST /api/architecture/reindex` — полная сборка (background)
- `POST /api/architecture/analyze` — инкрементальная сборка по `commit_sha`
- `GET /api/architecture/graph` — текущий граф (Redis → fallback ChromaDB)
- `GET /api/architecture/node/{id}` — детали узла
- `GET /api/architecture/diagram` — Mermaid
- `GET /api/architecture/diff` — последний diff (json)
- `POST /api/architecture/weights` — обновление весов (role/subsystem)
- `POST /api/architecture/tasks/sync` — синхронизация задач/таймлайна (docs/roadmap/GitHub)
- `GET /api/architecture/meta` — справочники/статистика
- `GET /api/faq/ai`, `POST /api/faq/ai` — RAG‑поиск по FAQ/докам

## Фронтенд (SPA)

- `/architecture`: React + D3/Vis.js
- Дерево: Role → Subsystem → Function → Tasks
- Граф: цвет=роль/подсистема, размер=вес; клик → детали узла, соседние функции, источник (файл:строки)
- Экспорт: PNG/SVG/Mermaid
- Гант: если у задач есть даты; иначе приоритетный таймлайн

## Итерации и шаги

### Итерация 1 — AST‑парсер, веса, сохранение
- Реализовать AST‑анализатор (функции/методы/роуты/вызовы)
- Классификация ролей/подсистем по путям + словарь ключевых слов
- Расчёт весов; нормализация степеней
- Сохранение: ChromaDB (коллекции arch_*), Redis (JSON‑срез), снапшоты JSON

### Итерация 2 — API
- Endpoints: reindex, analyze, graph, node, meta, weights, tasks‑sync, diagram, diff
- Atomics: безопасная подмена графа; дебаунс вебхуков

### Итерация 3 — SPA UI
- Реализация дерева, графа, фильтров, панели узла, экспорта

#### Статус (35%)
- Сделано: базовый рендер (Vis/D3), фильтры ролей/подсистем, раскраска, поиск, экспорт PNG/SVG/mermaid, панель деталей узла, легенда и формула веса.
- Проблемы UX: перегруженность графа, отсутствие кластеризации/иерархии, нет подсветки важных подграфов и кратких нарративов.

#### План улучшений (UI/UX)
- Кластеризация по подсистемам (сворачиваемые кластеры, подсчёт степеней внутри кластера).
- Иерархический layout (уровни: Role → Subsystem → Function), автофокус на выбранной роли.
- Сильные связи: подсветка топ‑N ребер по весу/частоте.
- Редуцирование графа: лимит по степени/весам, progressive disclosure.
- Быстрые пресеты (owner/manager/employee) и сценарии (например, «создание смены»).
- Экспорт в PDF с заголовком/легендой/датой снапшота.
- Быстрые ссылки «Открыть в Project Brain» / «Показать исходник».

### Итерация 4 — DevOps интеграция
#### Статус (70%)
- Сделано:
  - Project Brain → вебхуки в StaffProBot (`/api/admin/devops/brain/update`).
  - Раздел `/admin/devops/architecture`: снапшоты, diff, ссылка на визуализатор.
  - Кнопки запуска Analyze/Reindex из UI + авто‑определение BRAIN_URL.
  - Панель DevOps показывает «Последние события Brain».
- Осталось:
  - Ретраи/таймауты и журнал ошибок вебхуков.
  - RBAC/защита внутренних API экспорта.
  - Ссылки на артефакты (latest.json/diagram.mmd) из Brain.
  - Мини‑метрики Brain (время парсинга, узлы/рёбра динамика).

### Итерация 5 — Датасеты RAG
#### Статус (80%)
- Сделано:
  - Экспорт датасетов в StaffProBot (read-only API):
    - `/api/admin/devops/export/faq`, `/api/admin/devops/export/bugs`, `/api/admin/devops/export/changelog`.
  - В Project Brain: `POST /api/datasets/sync` — загрузка FAQ/Bugs/Changelog в ChromaDB (`faq_knowledge`, `bug_context`, `dev_changes`).
  - Кнопка Sync Datasets в `/admin/devops/architecture`.
  - Загрузка commit history (git log) в коллекцию `commit_history`.
  - Метрики датасетов: `GET /api/datasets/metrics`.
  - FAQ AI API: `GET/POST /api/faq/ai` (поиск по `faq_knowledge`).
- Осталось:
  - Векторизация (эмбеддинги) коллекций и обновление RAG индексов.
  - Инкрементальные обновления датасетов (по времени/ID) без полной перезаписи.
  - Метрики загрузки: количество документов по коллекциям, длительность, ошибки.

### Итерация 6 — CI/CD Unified Learning & Deploy
#### Статус (100%) — Завершена
- В StaffProBot `.github/workflows/main.yml` добавлены шаги:
  - Analyze Architecture (ретраи, fallback BRAIN_URL, выгрузка `latest.json`/`latest.mmd`, upload artifacts)
  - Sync Datasets (ретраи)
  - Deploy (SSH, health-check с 3 попытками, запись в `deployments` с `duration_seconds`)
  - Notify Telegram (статус CI/CD + краткая сводка Brain)
- DevOps UI: авто‑резолв BRAIN_URL (включая dev/prod), кнопки Analyze/Reindex/Sync Datasets.
- Документация обновлена: `staffprobot/doc/DEVOPS_COMMAND_CENTER.md`.

### Итерация 7 (опционально) — Neo4j
- Адаптер экспорта графа и сложные запросы влияния

## Контрольные проверки

- `curl http://localhost:8003/api/architecture/graph`
- `curl http://localhost:8003/api/faq/ai?q=ошибка`
- `curl http://localhost:8003/api/architecture/diff`

## Примечания

- ChromaDB — основной источник истины; Redis — ускоритель фронтенда; Neo4j — по необходимости.
- Соблюдать правила `doc/DOCUMENTATION_RULES.md` при добавлении/обновлении документации и эндпоинтов.


