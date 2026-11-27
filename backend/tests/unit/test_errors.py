"""Проверка единого формата ошибок (ТЗ, 3.4)."""

import pytest
from httpx import AsyncClient

from app.core.config import settings


async def test_not_implemented_returns_problem_json(client: AsyncClient) -> None:
    response = await client.get("/api/v1/journal/offerings")
    assert response.status_code == 501
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "not_implemented"
    assert body["status"] == 501


async def test_schedule_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/schedule?date_from=2027-02-01&date_to=2027-02-10")
    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"


@pytest.mark.parametrize("environment", ["stage", "prod"])
async def test_development_auth_is_disabled(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    monkeypatch.setattr(settings, "app_env", environment)
    response = await client.get(
        "/api/v1/schedule?date_from=2027-02-01&date_to=2027-02-10",
        headers={"Authorization": "Bearer test"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == "authentication_unavailable"


async def test_not_found_has_trace_id(client: AsyncClient) -> None:
    response = await client.get("/missing", headers={"X-Request-ID": "request-123"})
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert response.json()["trace_id"] == "request-123"


async def test_validation_has_trace_id(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/schedule?date_from=invalid&date_to=invalid", headers={"Authorization": "Bearer test"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
    assert response.json()["trace_id"] == response.headers["X-Request-ID"]


async def test_readiness_failure(client: AsyncClient, monkeypatch) -> None:
    from app.api.v1 import system

    async def fail(request) -> None:
        raise RuntimeError("secret detail")

    monkeypatch.setattr(system, "CHECKS", {"redis": fail})
    response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "unavailable"
    assert "secret detail" not in response.text


async def test_unexpected_error_is_safe(client: AsyncClient) -> None:
    from app.main import app

    async def fail() -> None:
        raise RuntimeError("private detail")

    app.add_api_route("/_test_error", fail, methods=["GET"])
    try:
        response = await client.get("/_test_error", headers={"X-Request-ID": "request-789"})
        assert response.status_code == 500
        assert response.json()["code"] == "internal_error"
        assert response.json()["trace_id"] == "request-789"
        assert "private detail" not in response.text
    finally:
        app.router.routes.pop()


async def test_generated_request_id(client: AsyncClient) -> None:
    from uuid import UUID

    response = await client.get("/health")
    UUID(response.headers["X-Request-ID"])


async def test_success_preserves_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "request-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"


async def test_invalid_body_returns_problem(client: AsyncClient) -> None:
    from fastapi import Body

    from app.main import app

    async def accept_number(value: int = Body()) -> dict[str, int]:
        return {"value": value}

    app.add_api_route("/_test_body", accept_number, methods=["POST"])
    try:
        response = await client.post("/_test_body", json="invalid")
        assert response.status_code == 400
        assert response.json()["code"] == "validation_error"
        assert response.headers["content-type"].startswith("application/problem+json")
    finally:
        app.router.routes.pop()


async def test_invalid_request_id_is_replaced(client: AsyncClient) -> None:
    from uuid import UUID

    response = await client.get("/health", headers={"X-Request-ID": "invalid value"})
    UUID(response.headers["X-Request-ID"])
