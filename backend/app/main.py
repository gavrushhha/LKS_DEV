"""Точка входа FastAPI-приложения."""

import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import Response

from app import __version__
from app.api.v1.router import api_router
from app.api.v1.system import ready
from app.core.config import settings
from app.core.errors import problem_response, register_exception_handlers
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    logger.info("app_started", env=settings.app_env, tandem_mode=settings.tandem_mode)
    # TODO(T3.3): инициализация пула Redis и подключения к источнику расписания
    yield
    logger.info("app_stopped")


app = FastAPI(
    title="ЛКС — Расписание и Журнал",
    version=__version__,
    description=("Витрина расписания над БД «Тандем.Университет» (только чтение) и журнал успеваемости ЛКС."),
    lifespan=lifespan,
    docs_url=None if settings.app_env == "prod" else "/docs",
    openapi_url=None if settings.app_env == "prod" else "/openapi.json",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: object) -> Response:
    from collections.abc import Awaitable, Callable
    from typing import cast

    import structlog

    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", incoming) else str(uuid4())
    request.state.trace_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=request_id)
    try:
        try:
            response = await cast(Callable[[Request], Awaitable[Response]], call_next)(request)
        except Exception:
            logger.exception("unhandled_exception")
            response = problem_response(500, "internal_error", "Internal Server Error", trace_id=request_id)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        structlog.contextvars.clear_contextvars()


register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["System"], summary="Живость процесса")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


app.add_api_route("/ready", ready, methods=["GET"], tags=["System"])
