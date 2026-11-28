"""Тестовые записи Т5.1. Здесь впоследствии заменяется источник данных."""

from pydantic import TypeAdapter

from app.schemas.dictionaries import DictionaryItem, DictionaryKind

_ITEMS: dict[DictionaryKind, list[dict[str, object]]] = {
    "groups": [
        {
            "id": "9167180b-d48f-4a43-8c7d-34f1ff25c7ee",
            "code": "TEST-01",
            "name": "Тестовая группа 1",
            "source_system": "mock",
            "extra": {},
        },
        {
            "id": "3e2546a3-30b5-47da-bafd-e5be5acc30d4",
            "code": "TEST-02",
            "name": "Тестовая группа 2",
            "source_system": "mock",
            "extra": {},
        },
    ],
    "teachers": [
        {
            "id": "1edb7240-85b2-4a22-92df-68a8b4bd4241",
            "code": "TEACHER-01",
            "name": "Тестовое имя преподавателя",
            "source_system": "mock",
            "extra": {},
        },
    ],
    "rooms": [
        {
            "id": "68cda925-f057-419b-b62b-f8b41b5be48f",
            "code": "ROOM-К_1",
            "name": "Тестовая аудитория К_1",
            "source_system": "mock",
            "extra": {},
        },
    ],
}


class MockDictionarySource:
    """Источник фиксированных данных для разработки Т5.1."""

    async def fetch(self, kind: DictionaryKind) -> list[DictionaryItem]:
        """Вернуть проверенные записи выбранного справочника."""
        # При каждом чтении создаются новые модели: ответы не меняют исходную заглушку.
        return TypeAdapter(list[DictionaryItem]).validate_python(_ITEMS[kind])
