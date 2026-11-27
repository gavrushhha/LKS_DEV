# Инвентарь API этапа 1

Список извлечён из действующего контракта `backend/openapi/openapi.yaml`. Это не подтверждение реализации. Существующие маршруты содержат заглушки; инвентарь нужен для согласования полного набора операций. Новое требование: API расписания читает локальный снимок в БД ЛКС; контракт синхронизации ещё не утверждён.

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/v1/schedule` | Расписание за период с фильтрами |
| GET | `/api/v1/schedule/entries/{entry_id}` | Карточка занятия |
| GET | `/api/v1/schedule/rooms/{room_id}/occupancy` | Занятость аудитории за день |
| GET | `/api/v1/schedule/bell-schedules` | Звонковое расписание |
| GET | `/api/v1/schedule/source-status` | Состояние источника расписания |
| GET | `/api/v1/journal/offerings` | Дисциплины, доступные для ведения журнала |
| GET | `/api/v1/journal/offerings/{offering_id}/lessons` | Занятия журнала по дисциплине |
| POST | `/api/v1/journal/offerings/{offering_id}/lessons` | Создать занятие в журнале |
| PATCH | `/api/v1/journal/lessons/{lesson_id}` | Изменить занятие — тема, тип, домашнее задание |
| GET | `/api/v1/journal/offerings/{offering_id}/grades` | Оценки по дисциплине |
| POST | `/api/v1/journal/offerings/{offering_id}/grades:bulk` | Массовая запись оценок |
| PATCH | `/api/v1/journal/grades/{grade_id}` | Изменить оценку |
| DELETE | `/api/v1/journal/grades/{grade_id}` | Удалить оценку |
| POST | `/api/v1/journal/offerings/{offering_id}/attendance:bulk` | Массовая отметка посещаемости |
| GET | `/api/v1/journal/offerings/{offering_id}/summary` | Сводка по дисциплине — БРС, пропуски, текущий рейтинг |
| GET | `/api/v1/journal/offerings/{offering_id}/history` | История изменений оценок и посещаемости |
| POST | `/api/v1/statements` | Сформировать ведомость |
| GET | `/api/v1/statements/{statement_id}` | Получить ведомость |
| GET | `/api/v1/statements/{statement_id}/pdf` | Скачать ведомость в PDF |
| POST | `/api/v1/statements/{statement_id}/close` | Закрыть ведомость |
| GET | `/api/v1/dictionaries/groups` | Учебные группы |
| GET | `/api/v1/dictionaries/disciplines` | Дисциплины |
| GET | `/api/v1/dictionaries/teachers` | Преподаватели |
| GET | `/api/v1/dictionaries/rooms` | Аудитории |
| GET | `/api/v1/dictionaries/grading-scales` | Шкалы оценивания |
| GET | `/health` | Проверка живости процесса |
| GET | `/ready` | Готовность зависимостей — БД ЛКС, БД Тандема, Redis, шина |

## Требует решения

- Определить, нужна ли отдельная операция запуска синхронизации, кто может её вызывать и как получать состояние; не объявлять неутверждённый endpoint реализованным.
- Подтвердить совместимость полей, UUID / ID Тандема, пагинации и ошибок с потребителями. Изменения контрактов проходят согласование.
- Контракт журнала и ведомостей приведён для полноты: реализация и запись через интеграционную шину — отдельные задачи.
