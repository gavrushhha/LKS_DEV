# Бэкенд ЛКС

## Т5.1 — справочники с кэшем

Реализованы на заглушках:
- `GET /api/v1/dictionaries/groups` — группы.
- `GET /api/v1/dictionaries/teachers` — преподаватели.
- `GET /api/v1/dictionaries/rooms` — аудитории.

Для каждого справочника — отдельный Redis-кэш на 60 секунд
(`DICTIONARY_CACHE_TTL_SECONDS`). При сбое или повреждении кэша ответ берётся из источника.
Модель `DictionaryItem` проверяет записи и описывает ответы API.

Слои: `api/v1/dictionaries.py` → `services/dictionary_service.py` →
`repositories/dictionary_repository.py` → `source/mock/dictionaries.py`.
Redis подключается через `core/dictionary_deps.py` и `core/dictionary_cache.py`.

Данные пока тестовые (`source_system: "mock"`). Для завершения интеграции нужно заменить
тестовый источник согласованным источником данных Тандема (например, его локальной копией в БД ЛКС).
Т5.2 и Т5.3 не реализованы. Режим авторизации для демо требует согласования команды.
