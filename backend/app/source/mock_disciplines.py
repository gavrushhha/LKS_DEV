"""Тестовые записи для справочника дисциплин."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DisciplineRecord:
    id: UUID
    name: str
    code: str | None


MOCK_DISCIPLINES: tuple[DisciplineRecord, ...] = (
    DisciplineRecord(
        id=UUID("7a7f4b9d-e63c-4bb0-8128-228459bc7765"),
        name="Математика",
        code="IT-01",
    ),
    DisciplineRecord(
        id=UUID("dc88539b-846f-4c83-aa4a-6cdaa197119e"),
        name="Основы IT",
        code="CS-02",
    ),
    DisciplineRecord(
        id=UUID("d0379984-3e92-402a-a8a7-1f7285d7281b"),
        name="История",
        code=None,
    ),
)
