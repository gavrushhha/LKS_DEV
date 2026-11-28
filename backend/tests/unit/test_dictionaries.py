"""Т5.1: API, кэш и восстановление после сбоев без внешнего Redis."""

import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from pydantic import TypeAdapter
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.dictionary_deps import get_dictionary_service
from app.main import app
from app.repositories.dictionary_repository import DictionaryRepository
from app.schemas.dictionaries import DictionaryItem, DictionaryKind
from app.services.dictionary_service import DictionaryService
from app.source.mock.dictionaries import MockDictionarySource

KINDS: tuple[DictionaryKind, ...] = ("groups", "teachers", "rooms")
ADAPTER = TypeAdapter(list[DictionaryItem])


class CountingSource(MockDictionarySource):
    def __init__(self) -> None:
        self.calls: list[DictionaryKind] = []
        self.fail = False

    async def fetch(self, kind: DictionaryKind) -> list[DictionaryItem]:
        self.calls.append(kind)
        if self.fail:
            raise RuntimeError("source unavailable")
        return await super().fetch(kind)


class MemoryCache:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expires: dict[str, int] = {}
        self.now = 0
        self.read_error = False
        self.write_error = False
        self.writes: list[tuple[str, int]] = []

    async def read(self, key: str) -> str | None:
        if self.read_error:
            raise RedisConnectionError("test read failure")
        if key in self.expires and self.now >= self.expires[key]:
            self.values.pop(key, None)
        return self.values.get(key)

    async def write(self, key: str, payload: str, ttl: int) -> None:
        if self.write_error:
            raise RedisConnectionError("test write failure")
        self.values[key] = payload
        self.expires[key] = self.now + ttl
        self.writes.append((key, ttl))


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "scenario",
    ["miss", "hit", "redis_down", "write_error", "bad_json", "bad_id", "bad_name"],
)
async def test_dictionary_api_cache(client: AsyncClient, kind: DictionaryKind, scenario: str) -> None:
    source = CountingSource()
    cache = MemoryCache()
    key = f"dictionaries:{kind}"
    expected = await MockDictionarySource().fetch(kind)
    if scenario == "hit":
        # Другое корректное имя доказывает, что вернулся именно кэш.
        cached_items = [item.model_copy(update={"name": "Из кэша"}) for item in expected]
        cache.values[key] = ADAPTER.dump_json(cached_items).decode()
        expected = cached_items
    elif scenario == "redis_down":
        cache.read_error = cache.write_error = True
    elif scenario == "write_error":
        cache.write_error = True
    elif scenario == "bad_json":
        cache.values[key] = "broken-json"
    elif scenario in ("bad_id", "bad_name"):
        record = expected[0].model_dump(mode="json")
        record["id" if scenario == "bad_id" else "name"] = "bad-id" if scenario == "bad_id" else 123
        cache.values[key] = json.dumps([record])

    service = DictionaryService(DictionaryRepository(source), cache, ttl=60)
    app.dependency_overrides[get_dictionary_service] = lambda: service
    try:
        response = await client.get(f"/api/v1/dictionaries/{kind}")
    finally:
        app.dependency_overrides.pop(get_dictionary_service, None)

    assert response.status_code == 200
    assert response.json() == [item.model_dump(mode="json") for item in expected]
    assert source.calls == ([] if scenario == "hit" else [kind])
    if scenario not in ("hit", "redis_down", "write_error"):
        assert cache.writes == [(key, 60)]
        assert ADAPTER.validate_json(cache.values[key]) == expected


@pytest.mark.parametrize("kind", KINDS)
async def test_dictionary_omits_missing_code(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, kind: DictionaryKind
) -> None:
    source = MockDictionarySource()
    item = (await source.fetch(kind))[0]
    record = item.model_dump(mode="json")
    without_code = {key: value for key, value in record.items() if key != "code"}
    without_code["extra"] = {"building": None}
    fetch = AsyncMock(
        return_value=[
            DictionaryItem.model_validate(without_code),
            DictionaryItem.model_validate({**without_code, "code": None}),
            item,
        ],
    )
    monkeypatch.setattr(source, "fetch", fetch)
    service = DictionaryService(DictionaryRepository(source), MemoryCache(), ttl=60)
    monkeypatch.setitem(app.dependency_overrides, get_dictionary_service, lambda: service)

    for _ in range(2):
        response = await client.get(f"/api/v1/dictionaries/{kind}")
        assert response.status_code == 200
        assert response.json() == [without_code, without_code, record]
    fetch.assert_awaited_once_with(kind)


async def test_cache_keys_and_expiration() -> None:
    source = CountingSource()
    cache = MemoryCache()
    service = DictionaryService(DictionaryRepository(source), cache, ttl=60)
    for kind in KINDS:
        assert await service.list_items(kind)
    assert set(cache.values) == {f"dictionaries:{kind}" for kind in KINDS}
    assert source.calls == list(KINDS)

    cache.now = 59
    for kind in KINDS:
        await service.list_items(kind)
    assert source.calls == list(KINDS)
    assert len(cache.writes) == 3

    cache.now = 60
    for kind in KINDS:
        await service.list_items(kind)
    assert source.calls == list(KINDS) * 2
    assert len(cache.writes) == 6


async def test_source_error_is_not_hidden() -> None:
    source = CountingSource()
    source.fail = True
    service = DictionaryService(DictionaryRepository(source), MemoryCache(), ttl=60)
    with pytest.raises(RuntimeError, match="source unavailable"):
        await service.list_items("groups")


def test_dictionary_openapi() -> None:
    schema = app.openapi()
    for kind, operation_id in zip(KINDS, ("listGroups", "listTeachers", "listRooms"), strict=True):
        operation = schema["paths"][f"/api/v1/dictionaries/{kind}"]["get"]
        assert operation["operationId"] == operation_id
        response_schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["items"]["$ref"] == "#/components/schemas/DictionaryItem"
    item = schema["components"]["schemas"]["DictionaryItem"]
    assert item["properties"]["id"]["format"] == "uuid"
    assert item["properties"]["name"]["type"] == "string"
    code = item["properties"]["code"]
    assert code["type"] == "string"
    assert "default" not in code
    assert "code" not in item["required"]
