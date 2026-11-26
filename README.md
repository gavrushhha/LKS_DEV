# LKS_DEV — личные кабинеты студентов

Монорепозиторий проекта ЛКС (Научно-технологический университет «Сириус»).

## Структура

```
backend/    REST API: FastAPI, Python 3.12, PostgreSQL, Redis
frontend/   интерфейсы ЛКС (React / Vue) — следующий этап
infra/      docker-compose, окружения, миграции окружений
docs/       ТЗ, ADR, схемы
```

## Этап 1 (текущий)

* `backend` — витрина расписания (read-only из БД «Тандем.Университет») и журнал успеваемости.
* Фронтенд не разрабатывается, контракты API фиксируются заранее.

Документы этапа:

* ТЗ: `docs/ТЗ_этап1_расписание_журнал.docx`
* Контракт: `backend/openapi/openapi.yaml` (OpenAPI 3.1)
* Бэклог: `docs/backlog/ЛКС_этап1_бэклог.xlsx`
* Функции чтения Тандема: `backend/app/source/tandem/README.md`

## Быстрый старт

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Проверка: `curl localhost:8000/health`, документация — `localhost:8000/docs`.

## Правила разработки

* Ветки короткоживущие, PR до 400 строк, обязательный ревью.
* `ruff`, `mypy --strict`, `pytest` — обязательны до пуша (pre-commit + CI).
* Запись в схему источника расписания (Тандем) запрещена: только SELECT. См. `docs/adr/0001`.
