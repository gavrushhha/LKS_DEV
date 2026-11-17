"""Доступ к БД ЛКС (схема education). Реализация — T6–T10."""

from typing import Any


class JournalRepository:
    async def list_offerings(self, teacher_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError("T7.1")

    async def list_lessons(self, offering_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError("T7.2")

    async def upsert_grades(self, offering_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError("T8.2")
