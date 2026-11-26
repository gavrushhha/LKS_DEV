"""Dependency readiness checks."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.errors import problem_response

router = APIRouter(tags=["System"])


async def check_database() -> None:
    engine = create_async_engine(settings.lks_db_dsn, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


async def check_redis() -> None:
    client = Redis.from_url(settings.redis_dsn)
    try:
        await client.ping()
    finally:
        await client.aclose()


@router.get("/ready", summary="Dependency readiness")
async def ready(request: Request) -> JSONResponse:
    checks = {}
    for name, check in (("lks_db", check_database), ("redis", check_redis)):
        try:
            await asyncio.wait_for(check(), timeout=3)
            checks[name] = "ok"
        except Exception:
            checks[name] = "unavailable"
    healthy = all(value == "ok" for value in checks.values())
    if not healthy:
        response = problem_response(
            503, "dependencies_unavailable", "Dependencies unavailable", trace_id=request.state.trace_id
        )
        return response
    return JSONResponse(content={"status": "ok", "checks": checks})
