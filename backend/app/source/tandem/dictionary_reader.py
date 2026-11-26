"""Чтение подтверждённых справочников Тандема по идентификатору."""

from dataclasses import dataclass
from datetime import datetime

from app.source.tandem import queries
from app.source.tandem.client import TandemClient


@dataclass(frozen=True)
class Group:
    id: str
    title: str | None
    short_title: str | None
    archived: bool | None


@dataclass(frozen=True)
class Room:
    id: str
    number: str | None
    title: str | None
    building_id: str | None


@dataclass(frozen=True)
class Teacher:
    id: str
    role_guid: str | None
    last_name: str | None
    first_name: str | None
    middle_name: str | None
    removal_date: datetime | None


class TandemDictionaryReader:
    """Функции для других слоёв приложения; доступ только на чтение."""

    def __init__(self, client: TandemClient) -> None:
        self._client = client

    async def group_by_id(self, group_id: int) -> Group | None:
        """Вернуть академическую группу или None, если её нет."""
        self._validate_id(group_id)
        rows = await self._client.fetch(queries.GROUP_BY_ID, group_id)
        if not rows:
            return None
        row = rows[0]
        return Group(str(row["id"]), row["title_p"], row["shorttitle_p"], row["archival_p"])

    async def groups_page(self, *, after_id: int | None = None, limit: int = 100) -> list[Group]:
        """Вернуть страницу групп по возрастанию ID источника."""
        self._validate_page(after_id, limit)
        rows = await self._client.fetch(queries.GROUPS_PAGE, after_id, limit)
        return [Group(str(r["id"]), r["title_p"], r["shorttitle_p"], r["archival_p"]) for r in rows]

    async def room_by_id(self, room_id: int) -> Room | None:
        """Вернуть аудиторию или None, если её нет."""
        self._validate_id(room_id)
        rows = await self._client.fetch(queries.ROOM_BY_ID, room_id)
        if not rows:
            return None
        row = rows[0]
        building_id = row["cachedbuilding_id"]
        return Room(
            str(row["id"]),
            row["number_p"],
            row["title_p"],
            str(building_id) if building_id is not None else None,
        )

    async def rooms_page(self, *, after_id: int | None = None, limit: int = 100) -> list[Room]:
        """Вернуть страницу аудиторий по возрастанию ID источника."""
        self._validate_page(after_id, limit)
        rows = await self._client.fetch(queries.ROOMS_PAGE, after_id, limit)
        return [
            Room(
                str(r["id"]),
                r["number_p"],
                r["title_p"],
                str(r["cachedbuilding_id"]) if r["cachedbuilding_id"] is not None else None,
            )
            for r in rows
        ]

    async def teacher_by_id(self, teacher_id: int) -> Teacher | None:
        """Вернуть преподавателя по ID роли или None, если его нет."""
        self._validate_id(teacher_id)
        rows = await self._client.fetch(queries.TEACHER_BY_ID, teacher_id)
        return self._teacher_from_row(rows[0]) if rows else None

    async def teachers_page(self, *, after_id: int | None = None, limit: int = 100) -> list[Teacher]:
        """Вернуть страницу преподавателей, включая записи без ФИО."""
        self._validate_page(after_id, limit)
        rows = await self._client.fetch(queries.TEACHERS_PAGE, after_id, limit)
        return [self._teacher_from_row(row) for row in rows]

    @staticmethod
    def _teacher_from_row(row: dict) -> Teacher:  # type: ignore[type-arg]
        return Teacher(
            str(row["id"]),
            row["guid_p"],
            row["lastname_p"],
            row["firstname_p"],
            row["middlename_p"],
            row["removaldate_p"],
        )

    @classmethod
    def _validate_page(cls, after_id: int | None, limit: int) -> None:
        if after_id is not None:
            cls._validate_id(after_id)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("Размер страницы должен быть от 1 до 200")

    @staticmethod
    def _validate_id(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 < value < 2**63:
            raise ValueError("ID должен быть положительным числом PostgreSQL bigint")
