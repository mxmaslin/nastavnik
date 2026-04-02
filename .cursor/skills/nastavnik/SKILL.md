---
name: nastavnik
description: >-
  Describes the Nastavnik monorepo (Django/DRF/Celery, FastAPI ML stub, Next.js, Docker Compose,
  RabbitMQ, Prometheus/Grafana). Use when editing nastavnik, running or debugging services, API
  contracts, migrations, frontend API URLs, tests, or release checklists. For full HTTP field lists see reference.md in the same folder.
---

# Nastavnik project skill

## Source of truth

- **Product spec & URLs**: [README.md](../../../README.md) (including «Что было навайбкодено»).
- **Agent checklist & stack summary**: [AGENTS.md](../../../AGENTS.md).

Do not contradict README without updating it.

## Layout

| Path | Role |
|------|------|
| `backend/` | Django project `nastavnik`, app `lessons`, Daphne ASGI, Celery worker image |
| `ml_service/` | FastAPI `/validate`, async SQLAlchemy + Redis cache |
| `frontend/` | Next.js App Router; в браузере API по умолчанию `http://<host>:8000`, опционально `NEXT_PUBLIC_API_URL` |
| `monitoring/` | Prometheus scrape config, Grafana datasource |

## Commands

```bash
make	up          # full stack
make	test        # backend pytest (+ eager Celery) + ml_service pytest
make	test-e2e   # Playwright (нужен backend :8000; Next поднимает webServer)
make	down / logs # operate compose
```

Backend container startup runs `migrate` and `seed_data` before Daphne.

## Domain rules (do not break silently)

- **`LessonSession`**: unique on `(session_id, lesson)` — same browser id can do different lessons.
- **`POST .../lessons/{id}/start/`**: returns question at **`current_question_index`**, not always the first. Если сессия по уроку уже **завершена**, повторный `start` **сбрасывает** попытку (удаляет `InteractionRecord` для пары session+lesson, индекс с нуля).
- **`GET /api/statistics/`**: опционально `lesson_id` + `session_id` — статистика только по одному уроку; без `lesson_id` — по всем данным сессии.
- **`POST .../answer/submit/`**: must submit the **current** question for that session; response includes `lesson_complete` when no next question.
- **`POST .../lessons/{id}/complete/`**: creates `InteractionRecord` rows (empty answer, `is_correct=False`) for unanswered questions; returns `remaining_marked_incorrect`.
- **Celery**: broker **RabbitMQ**; result backend **Redis** `/2`; cache/channels use Redis `/0` (see `docker-compose.yml`).

## API hints

- **Swagger UI:** `http://localhost:8000/api/schema/swagger-ui/` (OpenAPI из drf-spectacular).
- В сериализаторе вопроса поле **`choices`** (3 строки) для multiple-choice UI; проверка ответа по-прежнему по тексту выбранного варианта.
- Health: `http://localhost:8000/api/health/`.
- Metrics: Django `/metrics`, ML `/metrics` (Prometheus scrapes both).
- DRF throttling is enabled; heavy manual testing may hit limits.
- `GET /api/questions/current/` requires **`session_id` and `lesson_id`**.

## Frontend networking

- Открой **http://localhost:3000**; фронт ходит на **http://localhost:8000** для `/api/...`.
- Другой хост API: `NEXT_PUBLIC_API_URL`.

## Changing data model

1. Edit `backend/lessons/models.py`.
2. `docker compose exec backend python manage.py makemigrations lessons`
3. Commit migration files; `make up` apply `migrate`.

## Quality gate before finishing

- `make test` passes; при изменениях UI — `make test-e2e`.
- `make up` + smoke: lesson flow, ML delay/failures, stats.

## Additional resources

- **[reference.md](reference.md)** — контракты REST/ML, коды ответов, throttling, **чеклист релиза**.
