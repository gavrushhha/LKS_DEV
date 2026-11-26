"""Health and readiness checks."""

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready_unavailable(client: AsyncClient, monkeypatch) -> None:
    async def fail() -> None:
        raise ConnectionError("offline")

    monkeypatch.setattr("app.api.v1.system.check_database", fail)
    monkeypatch.setattr("app.api.v1.system.check_redis", fail)
    response = await client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["code"] == "dependencies_unavailable"
    assert response.json()["trace_id"] == response.headers["X-Request-ID"]


async def test_ready_ok(client: AsyncClient, monkeypatch) -> None:
    async def ok() -> None:
        pass

    monkeypatch.setattr("app.api.v1.system.check_database", ok)
    monkeypatch.setattr("app.api.v1.system.check_redis", ok)
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["checks"] == {"lks_db": "ok", "redis": "ok"}


async def test_request_id(client: AsyncClient) -> None:
    request_id = "550e8400-e29b-41d4-a716-446655440000"
    response = await client.get("/health", headers={"X-Request-ID": request_id})
    assert response.headers["X-Request-ID"] == request_id


async def test_invalid_request_id_replaced(client: AsyncClient) -> None:
    from uuid import UUID

    response = await client.get("/health", headers={"X-Request-ID": "invalid value"})
    UUID(response.headers["X-Request-ID"])
