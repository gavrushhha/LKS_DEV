"""Точка входа FastAPI-приложения."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("app_started", env=settings.app_env, tandem_mode=settings.tandem_mode)
    # TODO(T3.3): инициализация пула Redis и подключения к источнику расписания
    yield
    logger.info("app_stopped")


app = FastAPI(
    title="ЛКС — Расписание и Журнал",
    version=__version__,
    description=("Витрина расписания над БД «Тандем.Университет» (только чтение) и журнал успеваемости ЛКС."),
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"], summary="Живость процесса")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
