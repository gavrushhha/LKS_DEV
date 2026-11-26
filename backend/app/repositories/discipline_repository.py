"""Репозиторий справочника дисциплин."""

from app.source.mock_disciplines import MOCK_DISCIPLINES, DisciplineRecord


class DisciplineRepository:
    """Получает записи справочника из источника."""

    async def list_all(self) -> tuple[DisciplineRecord, ...]:
        """Возвращает все дисциплины из тестового источника."""
        return MOCK_DISCIPLINES