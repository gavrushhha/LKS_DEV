"""Проверка готовности зависимостей приложения."""

import asyncio
from collections.abc import Awaitable, Callable

import aio_pika
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import Problem, problem_response
from app.core.logging import get_logger

router = APIRouter(tags=["System"])
logger = get_logger(__name__)


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


async def check_database(request: Request) -> None:
    async with request.app.state.db.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def check_redis(request: Request) -> None:
    await request.app.state.redis.ping()


async def check_tandem(request: Request) -> None:
    engine = request.app.state.tandem
    if engine is None:
        raise RuntimeError("Источник расписания не настроен")
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def check_rabbitmq(request: Request) -> None:
    # Подключение создаётся при первом запросе и переиспользуется до завершения приложения.
    async with request.app.state.rabbitmq_lock:
        connection = request.app.state.rabbitmq
        if connection is None or connection.is_closed:
            connection = await aio_pika.connect_robust(settings.rabbitmq_dsn.get_secret_value())
            request.app.state.rabbitmq = connection
        channel = await connection.channel()
        await channel.close()


CHECKS: dict[str, Callable[[Request], Awaitable[None]]] = {
    "lks_db": check_database,
    "redis": check_redis,
    "rabbitmq": check_rabbitmq,
    "tandem_source": check_tandem,
}


@router.get(
    "/ready",
    summary="Готовность зависимостей",
    response_model=ReadinessResponse,
    responses={
        503: {
            "model": Problem,
            "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/Problem"}}},
        }
    },
)
async def ready(request: Request) -> JSONResponse:
    async def run_check(name: str, check: Callable[[Request], Awaitable[None]]) -> tuple[str, str]:
        try:
            await asyncio.wait_for(check(request), timeout=3)
            return name, "ok"
        except Exception:
            logger.warning("dependency_unavailable", dependency=name)
            return name, "unavailable"

    checks = dict(await asyncio.gather(*(run_check(name, check) for name, check in CHECKS.items())))
    if any(value != "ok" for value in checks.values()):
        return problem_response(
            503,
            "dependencies_unavailable",
            "Зависимости недоступны",
            trace_id=getattr(request.state, "trace_id", None),
            checks=checks,
        )
    return JSONResponse(content={"status": "ok", "checks": checks})
