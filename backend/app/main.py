"""Точка входа FastAPI-приложения."""

import asyncio
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app import __version__
from app.api.v1 import system
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import problem_response, register_exception_handlers
from app.core.logging import configure_logging, get_logger

configure_logging(settings.log_level)
logger = get_logger(__name__)


class HealthResponse(BaseModel):
    status: str
    version: str


class LKSApp(FastAPI):
    def openapi(self) -> dict[str, Any]:
        schema = super().openapi()
        # Успешный ответ /ready возвращается как JSONResponse, несмотря на класс ошибки маршрута.
        schema["paths"]["/ready"]["get"]["responses"]["200"]["content"].pop("application/problem+json", None)
        return schema


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("app_started", env=settings.app_env, tandem_mode=settings.tandem_mode)
    app.state.rabbitmq = None
    app.state.rabbitmq_lock = asyncio.Lock()
    app.state.db = create_async_engine(settings.lks_db_dsn.get_secret_value(), pool_pre_ping=True)
    app.state.redis = Redis.from_url(settings.redis_dsn.get_secret_value())
    tandem_dsn = settings.tandem_db_dsn.get_secret_value()
    app.state.tandem = create_async_engine(tandem_dsn, pool_pre_ping=True) if tandem_dsn else None
    try:
        yield
    finally:
        if app.state.rabbitmq is not None:
            await app.state.rabbitmq.close()
        await app.state.redis.aclose()
        await app.state.db.dispose()
        if app.state.tandem is not None:
            await app.state.tandem.dispose()
        logger.info("app_stopped")


app = LKSApp(
    title="ЛКС — Расписание и Журнал",
    version=__version__,
    description=("Витрина расписания над БД «Тандем.Университет» (только чтение) и журнал успеваемости ЛКС."),
    lifespan=lifespan,
    docs_url=None if settings.app_env == "prod" else "/docs",
    openapi_url=None if settings.app_env == "prod" else "/openapi.json",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", incoming) else str(uuid4())
    request.state.trace_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=request_id)
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled_exception")
            response = problem_response(
                500, "internal_error", "Внутренняя ошибка сервера", trace_id=request_id
            )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        structlog.contextvars.clear_contextvars()


register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"], summary="Живость процесса", response_model=HealthResponse)
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


app.include_router(system.router)
