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


## Локальная разработка в Windows (PowerShell)

Выполняйте команды из корня репозитория. Для Docker нужен запущенный Docker Desktop.

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build
```

В другом терминале проверьте `http://localhost:8000/health` и
`http://localhost:8000/ready`. Для остановки без удаления данных PostgreSQL:

```powershell
docker compose down
```

Не используйте `docker compose down -v`, если нужно сохранить локальную базу.

Для запуска проверок Python:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m ruff check app tests
python -m ruff format --check app tests
python -m mypy app
python -m pytest
cd ..
pre-commit install
pre-commit run --all-files
```

## Настройки и секреты

Настройки читаются из переменных окружения, `.env` и файлов `/run/secrets`.
Файлы секретов могут быть переданы внешним механизмом, например Vault Agent;
само приложение не подключается к Vault и не управляет ротацией секретов.
Значения PostgreSQL в Compose предназначены только для локальной разработки.
Для stage/prod требуется задать реальные подключения через безопасное окружение.
Настоящая проверка JWT ещё не реализована; в prod заглушка авторизации отключена.
Не публикуйте приложение с реальными пользователями до её реализации.
