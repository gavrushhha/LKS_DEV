"""Проверка доступности приложения."""

from httpx import AsyncClient

from app.api.v1 import system


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready_returns_checks(client: AsyncClient, monkeypatch) -> None:
    async def ok(request) -> None:
        pass

    monkeypatch.setattr(system, "CHECKS", {"lks_db": ok, "redis": ok})
    response = await client.get("/ready")
    assert response.status_code == 200
    assert "checks" in response.json()
