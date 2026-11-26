"""T5.2: HTTP-тесты поиска дисциплин."""

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("q", ["  it-01  ", "  t-0  "])
async def test_disciplines_search_by_code(client: AsyncClient, q: str) -> None:
    response = await client.get(
        "/api/v1/dictionaries/disciplines",
        params={"q": q},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == [
        {
            "id": "7a7f4b9d-e63c-4bb0-8128-228459bc7765",
            "name": "Математика",
            "code": "IT-01",
            "source_system": "mock",
            "extra": {},
        }
    ]


async def test_disciplines_search_by_name_without_code(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/dictionaries/disciplines",
        params={"q": "  ИСТ  "},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "d0379984-3e92-402a-a8a7-1f7285d7281b",
            "name": "История",
            "source_system": "mock",
            "extra": {},
        }
    ]


@pytest.mark.parametrize("q", [None, "", "   "])
async def test_disciplines_empty_query_returns_all(client: AsyncClient, q: str | None) -> None:
    if q is None:
        response = await client.get("/api/v1/dictionaries/disciplines")
    else:
        response = await client.get(
            "/api/v1/dictionaries/disciplines",
            params={"q": q},
        )

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [
        "История",
        "Математика",
        "Основы IT",
    ]


async def test_disciplines_search_without_matches(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/dictionaries/disciplines",
        params={"q": "несуществующая дисциплина"},
    )

    assert response.status_code == 200
    assert response.json() == []
