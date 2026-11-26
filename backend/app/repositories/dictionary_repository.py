"""Получение справочников независимо от конкретного источника."""

from typing import Protocol

from app.schemas.dictionaries import DictionaryItem, DictionaryKind


class DictionarySource(Protocol):
    async def fetch(self, kind: DictionaryKind) -> list[DictionaryItem]: ...


class DictionaryRepository:
    def __init__(self, source: DictionarySource) -> None:
        self._source = source

    async def list_items(self, kind: DictionaryKind) -> list[DictionaryItem]:
        return await self._source.fetch(kind)
