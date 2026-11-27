"""Проверка доступности приложения."""

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready_returns_checks(client: AsyncClient, monkeypatch) -> None:
    async def ok() -> None:
        pass

    monkeypatch.setattr("app.api.v1.system.check_database", ok)
    monkeypatch.setattr("app.api.v1.system.check_redis", ok)
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert "checks" in response.json()
