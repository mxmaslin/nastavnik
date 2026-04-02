# Agent Instructions for Nastavnik Project

## Источник постановки

Детальное описание продукта, стека и запуска — в **README.md** (включая секцию **«Что было навайбкодено»** и таблицу URL сервисов).

Краткий контекст для агента в Cursor: **`.cursor/skills/nastavnik/SKILL.md`** (детали API и чеклист релиза — **`reference.md`** рядом).

## Project structure (фактическая)

```
nastavnik/
├── backend/           # Django + DRF, Celery worker image, Daphne (ASGI)
├── frontend/          # Next.js (TypeScript)
├── ml_service/        # FastAPI
├── monitoring/        # Prometheus + Grafana provisioning
├── docker-compose.yml
├── Makefile
└── README.md
```

## Evaluation criteria (из ТЗ)

1. **Functionality (30%)** — запуск по README, сценарии урока и ML
2. **Code quality (25%)** — читаемость, конвенции
3. **Testing (20%)** — pytest (backend + ml_service), `make test`; E2E фронта — `make test-e2e` / job **e2e** в CI (Playwright)
4. **Documentation (10%)** — README, ясные инструкции
5. **Architecture (15%)** — разделение сервисов, очередь, кэш, БД

## Technical stack (как в репозитории)

- **Frontend**: Next.js
- **Backend**: Django, DRF, Channels/Daphne, Celery
- **Broker**: RabbitMQ (результаты Celery — Redis)
- **ML**: FastAPI, Redis + PostgreSQL (async SQLAlchemy в ML-сервисе)
- **Data**: PostgreSQL, Redis
- **Observability**: Prometheus, Grafana (`django-prometheus`, instrumentator на ML)
- **Deploy**: Docker Compose
- **Tests**: Pytest

## Quality gates

- Все сервисы поднимаются командой **`make up`**
- Основной сценарий урока и сохранение `interaction_records` работают
- **`make test`** проходит
- Документация в README актуальна

## Подсказка агенту

При доработках опирайся на **README.md**, не раздуливай скоуп сверх постановки; после изменений прогоняй тесты в Docker (`make test`).
