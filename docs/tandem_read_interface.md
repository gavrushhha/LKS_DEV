# Интерфейс чтения из Тандема (черновик)

Слой `app.source.tandem` предоставляет асинхронные функции чтения. Данные не записываются в БД Тандема и не копируются в БД ЛКС. Интерфейс и соответствие данным нужно согласовать с владельцами API и проверить на источнике.

## Подключение

В FastAPI зависимость `get_tandem_client(request)` получает общий клиент из состояния приложения и подключает его при первом вызове. При остановке приложения пул закрывается. Для самостоятельного использования:

```python
from app.source.tandem.client import TandemClient
from app.source.tandem.dictionary_reader import TandemDictionaryReader

client = TandemClient()
await client.connect()
try:
    reader = TandemDictionaryReader(client)
    group = await reader.group_by_id(123)
finally:
    await client.close()
```

Клиенту нужен DSN отдельного read-only пользователя в настройках приложения. Конкретные адреса и пароли в код или Git не добавляются. Права необходимо проверить на самой БД.

## Справочники

`TandemDictionaryReader(client)` возвращает dataclass, при отсутствии объекта — `None`:

| Метод | Параметры | Результат |
|---|---|---|
| `group_by_id` | `group_id: int` | `Group \| None`: `id`, `title`, `short_title`, `archived` |
| `room_by_id` | `room_id: int` | `Room \| None`: `id`, `number`, `title`, `building_id` |
| `teacher_by_id` | `teacher_id: int` | `Teacher \| None`: `id`, `role_guid`, `last_name`, `first_name`, `middle_name`, `removal_date` |
| `groups_page` | `after_id: int \| None`, `limit: int` | `list[Group]` |
| `rooms_page` | `after_id: int \| None`, `limit: int` | `list[Room]` |
| `teachers_by_name` | `first_name: str`, `last_name: str`, `after_id: int \| None`, `limit: int` | `list[Teacher]` |
| `disciplines_by_title` | `query: str`, `after_id: int \| None`, `limit: int` | `list[RegistryElement]` |
| `disciplines_page` | `after_id: int \| None`, `limit: int` | `list[RegistryElement]` |
| `registry_elements_page` | `after_id: int \| None`, `limit: int` | `list[RegistryElement]` |
| `teachers_page` | `after_id: int \| None`, `limit: int` | `list[Teacher]` |

Параметры страниц передаются по имени. `limit` по умолчанию 100, максимум 200. Результат упорядочен по числовому ID; для следующей страницы передать `int(items[-1].id)`. Последняя страница может содержать ровно `limit` элементов: следующая в таком случае окажется пустой. Автоматический фильтр архивных групп и выбывших преподавателей отсутствует. Отсутствующие ФИО и названия могут быть `None`.

Входные ID — положительные целые PostgreSQL bigint; выходные ID представлены строками. UUID роли преподавателя возвращается отдельно и его заполненность и уникальность на всех данных не подтверждены. В локально сохранённой ветке T5 модель ответа ожидает UUID и метод `fetch(kind)` без пагинации: прямой совместимости нет, формат и адаптацию нужно согласовать. Поиск преподавателей по имени и фамилии точный, без учёта регистра, может вернуть несколько совпадений и включает выбывших. Проверка SQL на реальной БД и его план пока не выполнены. registry_elements_page возвращает общие записи реестра; disciplines_page отбирает записи, связанные с epp_reg_discipline_t. Какое поле является кодом API и какие дисциплины следует исключать, пока не подтверждено. disciplines_by_title ищет буквальную подстроку названия без учёта регистра; пустой запрос отклоняется. Поиск по коду не реализован, сравнение строк и планы необходимо проверить на реальной БД.

## Расписание

`TandemScheduleReader(client).fetch(kind, source_id, date_from, date_to, limit=50)` возвращает исходные строки, а `fetch_core(...)` — подтверждённые поля `ScheduleCore`. `kind`: `group`, `teacher`, `room` или `student`; `source_id` — числовой ID Тандема. Период включителен, максимум 92 дня; `limit` 1–200. `ScheduleCore` содержит `id`, `date`, `pair_number`, `starts_at`, `ends_at`, `updated_at`, `fetched_at`. При отсутствии номера пары выдаётся ошибка. Структура не является полным API-ответом.

Для группы один SQL проверен на реальной БД: 46 строк за две недели, один замер — 77 мс. Это не проверка остальных запросов или p95. Основная версия с пустыми датами рассматривается как не имеющая соответствующих границ — это предположение требует подтверждения. Не подтверждены семантика отмен, чётность, история состава групп и часовой пояс времени обновления. SQL и планы требуют согласования с владельцем источника. Эндпоинты API к функциям пока не подключены.
