"""HTTP-маршруты справочников. Получение данных и кэширование — в сервисе."""

from fastapi import APIRouter

from app.core.dictionary_deps import DictionaryServiceDep
from app.repositories.discipline_repository import DisciplineRepository
from app.schemas.dictionaries import DictionaryItem
from app.services.discipline_service import DisciplineService

router = APIRouter(prefix="/dictionaries", tags=["Dictionaries"])


@router.get("/groups", summary="Учебные группы", operation_id="listGroups", response_model_exclude_none=True)
async def list_groups(service: DictionaryServiceDep) -> list[DictionaryItem]:
    return await service.list_items("groups")


@router.get("/disciplines", summary="Дисциплины", operation_id="listDisciplines", response_model_exclude_none=True)
async def list_disciplines(q: str | None = None) -> list[DictionaryItem]:
    repository = DisciplineRepository()
    service = DisciplineService(repository)
    return await service.list_items(q)


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
