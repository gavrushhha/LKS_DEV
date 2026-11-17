"""Служебные эндпоинты."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["System"])


@router.get("/ready", summary="Готовность зависимостей")
async def ready() -> dict[str, object]:
    """TODO(T1.5): реальные проверки БД ЛКС, Redis, источника расписания."""
    return {
        "status": "ok",
        "checks": {
            "lks_db": "not_configured",
            "redis": "not_configured",
            "tandem_source": settings.tandem_mode,
        },
    }
