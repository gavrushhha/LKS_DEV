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

## Быстрый старт

```bash
cp .env.example .env
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000 --env-file ../.env
```

Проверка: `curl localhost:8000/health`, документация — `localhost:8000/docs`.

Файл `.env` в корне используется и Docker Compose, и этой командой запуска. В примере
адрес источника расписания указан как заглушка: `/ready` вернёт ошибку, пока не будет
настроен доступный `TANDEM_DB_DSN`.

## Правила разработки

* Ветки короткоживущие, PR до 400 строк, обязательный ревью.
* `ruff`, `mypy --strict`, `pytest` — обязательны до пуша (pre-commit + CI).
* Запись в схему источника расписания (Тандем) запрещена: только SELECT. См. `docs/adr/0001`.
