"""Справочники (ТЗ, раздел 5, эндпоинты dictionaries)."""

from fastapi import APIRouter

router = APIRouter(prefix="/dictionaries", tags=["Dictionaries"])


@router.get("/groups", summary="Учебные группы")
async def list_groups() -> list[dict[str, object]]:
    """TODO(T5.1)."""
    raise NotImplementedError


@router.get("/disciplines", summary="Дисциплины")
async def list_disciplines(q: str | None = None) -> list[dict[str, object]]:
    """TODO(T5.2)."""
    raise NotImplementedError(q)


@router.get("/teachers", summary="Преподаватели")
async def list_teachers() -> list[dict[str, object]]:
    """TODO(T5.1)."""
    raise NotImplementedError


@router.get("/rooms", summary="Аудитории")
async def list_rooms() -> list[dict[str, object]]:
    """TODO(T5.1)."""
    raise NotImplementedError


@router.get("/grading-scales", summary="Шкалы оценивания")
async def list_grading_scales() -> list[dict[str, object]]:
    """TODO(T5.3)."""
    raise NotImplementedError
