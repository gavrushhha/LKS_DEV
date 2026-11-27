"""Проверка единого формата ошибок (ТЗ, 3.4)."""

from httpx import AsyncClient


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
