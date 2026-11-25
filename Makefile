.PHONY: install dev lint type test up down migrate openapi

install:
	cd backend && pip install -e ".[dev]"

dev:
	cd backend && uvicorn app.main:app --reload --port 8000

lint:
	cd backend && ruff check app tests && ruff format --check app tests

type:
	cd backend && mypy app

test:
	cd backend && pytest -q

up:
	docker compose up -d --build

down:
	docker compose down -v

migrate:
	cd backend && alembic upgrade head

openapi:
	cd backend && python scripts/export_openapi.py
