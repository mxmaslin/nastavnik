# Nastavnik: справочник API и релиза

Все пути Django ниже — с префиксом **`/api/`** (напрямую: `http://localhost:8000/api/...`). Ответы — JSON, UUID в строках.

---

## Django / DRF

### Пагинация списков

`GET` с коллекциями (lessons) возвращает формат DRF:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

### Lessons

| Метод | Путь | Тело / query | Успех |
|--------|------|----------------|--------|
| GET | `/api/lessons/` | — | 200, пагинированный список (`id`, `title`, `question_count`, `created_at`) |
| GET | `/api/lessons/{lesson_uuid}/` | — | 200, урок с `questions[]` (`id`, `text`, `order`, `choices`) и `text` урока |
| POST | `/api/lessons/{lesson_uuid}/start/` | `{ "session_id": "<optional string>" }` | 200, см. ниже; повтор после **завершённой** сессии — новая попытка (сброс ответов по этой паре session+lesson) |
| POST | `/api/lessons/{lesson_uuid}/complete/` | `{ "session_id": "<required>" }` | 200, см. ниже; 400/404 |

**Ответ `start` (200):**

```json
{
  "session_id": "...",
  "lesson": { "id", "title", "text", "questions", "created_at" },
  "current_question": { "id", "text", "order", "choices": ["...", "...", "..."] },
  "current_question_index": 0,
  "total_questions": 0
}
```

`choices` — три варианта (верный + два `distractor_*`), порядок стабилен для `id` вопроса. Поля `correct_answer` и дистракторы в ответ API не входят.

`current_question` может быть `null`, если вопросы закончились.

**Ответ `complete` (200):**

```json
{
  "success": true,
  "success_rate": 0.0,
  "remaining_marked_incorrect": 0
}
```

### Questions

| Метод | Путь | Query | Успех |
|--------|------|--------|--------|
| GET | `/api/questions/current/` | `session_id`, `lesson_id` (обязательны) | 200, см. ниже; 400/404 |

**Ответ (200):**

```json
{
  "current_question": { "id", "text", "order", "choices": ["...", "...", "..."] },
  "current_question_index": 0,
  "total_questions": 0,
  "is_completed": false
}
```

`current_question` может быть `null`.

### Ответ пользователя

| Метод | Путь | Тело | Успех |
|--------|------|------|--------|
| POST | `/api/answer/submit/` | `{ "session_id", "question_id", "answer" }` (`answer` может быть `""`) | 200, см. ниже; 400/404 |

**Ответ (200):**

```json
{
  "interaction_id": "<uuid>",
  "status": "processing",
  "next_question": { "id", "text", "order", "choices": ["...", "...", "..."] },
  "current_question_index": 0,
  "total_questions": 0,
  "lesson_complete": false
}
```

`next_question` может быть `null` на последнем вопросе.

Ошибки 400 (примеры): не тот `question_id` для текущего шага; сессия завершена; вопрос не из урока сессии.

### Статус валидации (после submit)

| Метод | Путь | Успех |
|--------|------|--------|
| GET | `/api/answer/status/{interaction_uuid}/` | 200; 404 |

**Ответ (200)** — поля `InteractionRecord`:

`id`, `session_id`, `question` (UUID), `question_text`, `user_answer`, `is_correct` (`true` / `false` / `null`), `ml_service_success`, `response_time`, `answered_at`.

### Статистика

| Метод | Путь | Query | Успех |
|--------|------|--------|--------|
| GET | `/api/statistics/` | `session_id` — опционально; `lesson_id` — опционально (тогда **обязателен** `session_id`) | 200; 400 если задан только `lesson_id` без `session_id` или невалидный UUID |

**Ответ (200):**

`total_sessions`, `completed_sessions`, `total_questions_answered`, `correct_answers`, `success_rate`, `ml_failures`, `timeouts`, `ml_successful_validations`, `avg_session_duration_sec`, **`scope`**: `"all"` \| `"lesson"`, **`lesson_title`**: string \| null.

Без `lesson_id` — агрегат по всем урокам (в рамках `session_id`, если передан). С `lesson_id` — только по этому уроку и сессии.

### Прочее Django

| Метод | Путь | Назначение |
|--------|------|-------------|
| GET | `/` | Подсказка в браузере: фронт на :3000, ссылки на API / admin / Swagger |
| GET | `/api/health/` | `{ "status": "ok" }` |
| GET | `/api/schema/` | OpenAPI 3 (YAML) |
| GET | `/api/schema/swagger-ui/` | **Swagger UI** (интерактивная документация) |
| GET | `/metrics/` | Prometheus (корень сайта, не под `/api/`) |

**Админка:** `http://localhost:8000/admin/`.

Раньше Swagger не был подключён; сейчас схема строится через **drf-spectacular** из DRF viewsets и `@api_view`.

### Throttling

При частых запросах возможен **429** (DRF `AnonRateThrottle` / `UserRateThrottle`). См. `REST_FRAMEWORK` в `backend/nastavnik/settings.py`.

---

## ML-сервис (FastAPI)

База по умолчанию: `http://localhost:8001` (в Docker — `http://ml_service:8001`).

| Метод | Путь | Тело / ответ |
|--------|------|----------------|
| GET | `/health` | `{ "status": "ok" }` |
| GET | `/metrics` | Prometheus |
| POST | `/validate` | Request: `{ "question_id": "<uuid string>", "user_answer": "<string>" }` |

**Успех `POST /validate` (200):** `{ "result": 1 | 0 }`.

**Поведение:**

- не менее **~5 с** задержки на запрос;
- с вероятностью **~1/3** — **503** («LLM недоступна»);
- сравнение ответа: Redis (`answer:{question_id}`), при промахе — строка `correct_answer` из `lessons_question` (async SQLAlchemy), затем запись в Redis TTL 3600.

---

## Чеклист релиза (ручной)

Скопируй и отмечай:

```
[ ] make test — зелёный (backend + ml_service); CI / make test-e2e — Playwright при поднятом API
[ ] docker compose config — без ошибок
[ ] make up — backend healthy, celery без падений, seed есть данные
[ ] http://localhost:3000 — старт урока, ответ, таймаут пустого ответа, досрочное завершение
[ ] После прохождения — статистика только по уроку; с главной — статистика по всем пройденным
[ ] Повтор того же урока после завершения — новая попытка без ошибки загрузки
[ ] http://localhost:9090 — targets django / ml_service UP (после трафика)
[ ] Миграции закоммичены, нет расхождений models vs БД
[ ] README: порты и команды актуальны
[ ] При изменении API — обновлён reference.md (или SKILL.md)
```

Для публикации репозитория: убедиться, что **GitHub Actions** проходит на ветке по умолчанию.
