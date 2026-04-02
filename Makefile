.PHONY: up down build test test-e2e logs logs-backend logs-frontend logs-ml restart clean shell-backend shell-db shell-redis

# Идемпотентность: повторный запуск той же цели не должен падать с ошибкой, если это не нарушает смысл цели.

COMPOSE ?= docker-compose

up:
	$(COMPOSE) up -d --build --remove-orphans

down:
	$(COMPOSE) down --remove-orphans

build:
	$(COMPOSE) build

# Поднимает зависимости для тестов, затем pytest (повторный make test без предварительного up).
test:
	$(COMPOSE) up -d --build db redis rabbitmq backend ml_service
	$(COMPOSE) exec -T -e CELERY_TASK_ALWAYS_EAGER=1 backend pytest
	$(COMPOSE) exec -T ml_service pytest

# Playwright E2E: backend должен слушать :8000 (например make up). Next поднимет сам playwright webServer на :3000.
test-e2e:
	cd frontend && npm install && npx playwright install chromium && npx playwright test

logs:
	@if [ -n "$$($(COMPOSE) ps -q 2>/dev/null)" ]; then \
		$(COMPOSE) logs -f; \
	else \
		echo "$(COMPOSE): нет запущенных контейнеров (сначала make up)"; \
	fi

logs-backend:
	@if [ -n "$$($(COMPOSE) ps -q backend celery 2>/dev/null)" ]; then \
		$(COMPOSE) logs -f backend celery; \
	else \
		echo "$(COMPOSE): backend/celery не запущены"; \
	fi

logs-frontend:
	@if [ -n "$$($(COMPOSE) ps -q frontend 2>/dev/null)" ]; then \
		$(COMPOSE) logs -f frontend; \
	else \
		echo "$(COMPOSE): frontend не запущен"; \
	fi

logs-ml:
	@if [ -n "$$($(COMPOSE) ps -q ml_service 2>/dev/null)" ]; then \
		$(COMPOSE) logs -f ml_service; \
	else \
		echo "$(COMPOSE): ml_service не запущен"; \
	fi

# Если контейнеров ещё не было — поднимаем стек вместо ошибки «nothing to restart».
restart:
	@$(COMPOSE) restart || $(COMPOSE) up -d --remove-orphans

clean:
	$(COMPOSE) down -v --remove-orphans

shell-backend:
	$(COMPOSE) up -d backend
	$(COMPOSE) exec backend bash

shell-db:
	$(COMPOSE) up -d db
	$(COMPOSE) exec db psql -U nastavnik nastavnik

shell-redis:
	$(COMPOSE) up -d redis
	$(COMPOSE) exec redis redis-cli
