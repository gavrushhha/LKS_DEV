"""Журнал успеваемости (ТЗ, раздел 6)."""

from fastapi import APIRouter

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.get("/offerings", summary="Дисциплины для ведения журнала")
async def list_offerings() -> dict[str, object]:
    """TODO(T7.1)."""
    raise NotImplementedError


@router.get("/offerings/{offering_id}/lessons", summary="Занятия по дисциплине")
async def list_lessons(offering_id: str) -> list[dict[str, object]]:
    """TODO(T7.2)."""
    raise NotImplementedError(offering_id)


@router.post("/offerings/{offering_id}/lessons", status_code=201, summary="Создать занятие")
async def create_lesson(offering_id: str) -> dict[str, object]:
    """TODO(T7.3): проверка пары через модуль расписания, флаг extra."""
    raise NotImplementedError(offering_id)


@router.patch("/lessons/{lesson_id}", summary="Изменить занятие")
async def patch_lesson(lesson_id: str) -> dict[str, object]:
    """TODO(T7.4): окно 30 дней, If-Match."""
    raise NotImplementedError(lesson_id)


@router.get("/offerings/{offering_id}/grades", summary="Оценки по дисциплине")
async def list_grades(offering_id: str) -> list[dict[str, object]]:
    """TODO(T8.1)."""
    raise NotImplementedError(offering_id)


@router.post("/offerings/{offering_id}/grades:bulk", summary="Массовая запись оценок")
async def bulk_upsert_grades(offering_id: str) -> dict[str, object]:
    """TODO(T8.2): Idempotency-Key, частичный успех, до 500 записей."""
    raise NotImplementedError(offering_id)


@router.patch("/grades/{grade_id}", summary="Изменить оценку")
async def patch_grade(grade_id: str) -> dict[str, object]:
    """TODO(T8.3): обязательный комментарий через 24 ч и при понижении."""
    raise NotImplementedError(grade_id)


@router.delete("/grades/{grade_id}", status_code=204, summary="Удалить оценку")
async def delete_grade(grade_id: str) -> None:
    """TODO(T8.4): мягкое удаление с причиной."""
    raise NotImplementedError(grade_id)


@router.post("/offerings/{offering_id}/attendance:bulk", summary="Массовая отметка посещаемости")
async def bulk_upsert_attendance(offering_id: str) -> dict[str, object]:
    """TODO(T9.1): до 200 записей."""
    raise NotImplementedError(offering_id)


@router.get("/offerings/{offering_id}/summary", summary="Сводка и БРС")
async def get_summary(offering_id: str) -> dict[str, object]:
    """TODO(T11.3)."""
    raise NotImplementedError(offering_id)


@router.get("/offerings/{offering_id}/history", summary="История изменений")
async def get_history(offering_id: str) -> list[dict[str, object]]:
    """TODO(T10.3)."""
    raise NotImplementedError(offering_id)
