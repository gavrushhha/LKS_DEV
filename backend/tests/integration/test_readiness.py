"""Проверка подключений к тестовым сервисам."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("LKS_RUN_INTEGRATION") != "1", reason="Не запущены тестовые сервисы")
async def test_readiness_with_services() -> None:
    # Для теста CI использует отдельные PostgreSQL, Redis и RabbitMQ.
    # PostgreSQL также имитирует доступный источник расписания.
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["checks"] == {
        "lks_db": "ok",
        "redis": "ok",
        "rabbitmq": "ok",
        "tandem_source": "ok",
    }
