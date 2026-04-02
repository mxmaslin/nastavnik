.PHONY: up down build test logs restart clean

up:
	docker-compose up -d --build

down:
	docker-compose down

build:
	docker-compose build

test:
	docker-compose exec -e CELERY_TASK_ALWAYS_EAGER=1 backend pytest
	docker-compose exec ml_service pytest

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend celery

logs-frontend:
	docker-compose logs -f frontend

logs-ml:
	docker-compose logs -f ml_service

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker-compose rm -f

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec db psql -U nastavnik nastavnik

shell-redis:
	docker-compose exec redis redis-cli
