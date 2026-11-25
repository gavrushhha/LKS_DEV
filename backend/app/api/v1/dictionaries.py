"""Справочники (ТЗ, раздел 5, эндпоинты dictionaries)."""

import json
from fastapi import APIRouter
from redis.asyncio import Redis
from app.core.config import settings

router = APIRouter(prefix="/dictionaries", tags=["Dictionaries"])

@router.get("/groups", summary="Учебные группы")
async def list_groups() -> list[dict[str, object]]:
    """Возвращает тестовый список групп."""
    async with Redis.from_url(
        settings.redis_dsn,
        decode_responses=True,
    ) as redis:
        cached = await redis.get("dictionaries:groups")

        if cached is not None:
            return json.loads(cached)
        
        groups = [
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
        ]

        await redis.set(
            "dictionaries:groups",
            json.dumps(groups, ensure_ascii=False),
            ex=60,
        )
        return groups


@router.get("/disciplines", summary="Дисциплины")
async def list_disciplines(q: str | None = None) -> list[dict[str, object]]:
    """TODO(T5.2)."""
    raise NotImplementedError(q)


@router.get("/teachers", summary="Преподаватели")
async def list_teachers() -> list[dict[str, object]]:
    """Возвращает тестовый список преподавателей."""
    async with Redis.from_url(
        settings.redis_dsn,
        decode_responses=True,
    ) as redis:
        cached = await redis.get("dictionaries:teachers")

        if cached is not None:
            return json.loads(cached)

        teachers = [
            {
                "id": "1edb7240-85b2-4a22-92df-68a8b4bd4241",
                "code": "TEACHER-01",
                "name": "Тестовое имя преподавателя",
                "source_system": "mock",
                "extra": {},
            },
        ]

        await redis.set(
            "dictionaries:teachers",
            json.dumps(teachers, ensure_ascii=False),
            ex=60,
        )

        return teachers


@router.get("/rooms", summary="Аудитории")
async def list_rooms() -> list[dict[str, object]]:
    """Возвращает тестовые аудитории с кэшированием."""
    async with Redis.from_url(
        settings.redis_dsn,
        decode_responses=True,
    ) as redis:
        cached = await redis.get("dictionaries:rooms")

        if cached is not None:
            return json.loads(cached)

        rooms = [
            {
                "id": "68cda925-f057-419b-b62b-f8b41b5be48f",
                "code": "ROOM-К_1",
                "name": "Тестовая аудитория К_1",
                "source_system": "mock",
                "extra": {},
            },
        ]

        await redis.set(
            "dictionaries:rooms",
            json.dumps(rooms, ensure_ascii=False),
            ex=60,
        )

        return rooms

@router.get("/grading-scales", summary="Шкалы оценивания")
async def list_grading_scales() -> list[dict[str, object]]:
    """TODO(T5.3)."""
    raise NotImplementedError
