"""HTTP-маршруты справочников. Получение данных и кэширование — в сервисе."""

from fastapi import APIRouter

from app.core.dictionary_deps import DictionaryServiceDep
from app.schemas.dictionaries import DictionaryItem

router = APIRouter(prefix="/dictionaries", tags=["Dictionaries"])


@router.get("/groups", summary="Учебные группы", operation_id="listGroups", response_model_exclude_none=True)
async def list_groups(service: DictionaryServiceDep) -> list[DictionaryItem]:
    return await service.list_items("groups")


@router.get("/disciplines", summary="Дисциплины")
async def list_disciplines(q: str | None = None) -> list[dict[str, object]]:
    """TODO(T5.2)."""
    raise NotImplementedError(q)


@router.get(
    "/teachers", summary="Преподаватели", operation_id="listTeachers", response_model_exclude_none=True
)
async def list_teachers(service: DictionaryServiceDep) -> list[DictionaryItem]:
    return await service.list_items("teachers")


@router.get("/rooms", summary="Аудитории", operation_id="listRooms", response_model_exclude_none=True)
async def list_rooms(service: DictionaryServiceDep) -> list[DictionaryItem]:
    return await service.list_items("rooms")


@router.get("/grading-scales", summary="Шкалы оценивания")
async def list_grading_scales() -> list[dict[str, object]]:
    """TODO(T5.3)."""
    raise NotImplementedError
