"""Поиск и сортировка дисциплин."""

from app.repositories.discipline_repository import DisciplineRepository
from app.schemas.dictionaries import DictionaryItem


class DisciplineService:
    """Применяет правила поиска к записям репозитория."""

    def __init__(self, repository: DisciplineRepository) -> None:
        self._repository = repository

    async def list_items(self, q: str | None = None) -> list[DictionaryItem]:
        """Возвращает дисциплины, подходящие под строку поиска."""
        records = await self._repository.list_all()

        query = ""
        if q is not None:
            query = q.strip().casefold()

        items: list[DictionaryItem] = []

        for record in records:
            name_matches = query in record.name.casefold()

            code_matches = False
            if record.code is not None:
                code_matches = query in record.code.casefold()

            if query and not (name_matches or code_matches):
                continue

            item = DictionaryItem(
                id=record.id,
                name=record.name,
                code=record.code,
                source_system="mock",
                extra={},
            )
            items.append(item)

        items.sort(key=lambda item: (item.name.casefold(), item.id))

        return items