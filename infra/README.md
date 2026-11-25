# Инфраструктура

* `../docker-compose.yml` — локальное окружение (PostgreSQL, Redis, api).
* Окружения stage/prod ведутся в инфраструктурном репозитории; здесь только
  контракты: переменные окружения (`.env.example`), health/ready, миграции.

## Порядок выката

1. Применить миграции БД ЛКС: `alembic upgrade head`.
2. Проверить `/ready` — все зависимости `ok`.
3. Проверить `/api/v1/schedule/source-status`: `is_stale=false`, приемлемый `lag_seconds`.
