"""Справочники: проверенный кэш → репозиторий → обновление кэша."""

from typing import Protocol

from pydantic import TypeAdapter, ValidationError
from redis.exceptions import RedisError

from app.core.logging import get_logger
from app.repositories.dictionary_repository import DictionaryRepository
from app.schemas.dictionaries import DictionaryItem, DictionaryKind

logger = get_logger(__name__)
_adapter = TypeAdapter(list[DictionaryItem])


class DictionaryCache(Protocol):
    async def read(self, key: str) -> str | None: ...

    async def write(self, key: str, payload: str, ttl: int) -> None: ...


class DictionaryService:
    def __init__(self, repository: DictionaryRepository, cache: DictionaryCache, ttl: int) -> None:
        self._repository = repository
        self._cache = cache
        self._ttl = ttl

    async def list_items(self, kind: DictionaryKind) -> list[DictionaryItem]:
        key = f"dictionaries:{kind}"
        try:
            cached = await self._cache.read(key)
            if cached is not None:
                return _adapter.validate_json(cached)
        except (RedisError, ValidationError, UnicodeDecodeError) as exc:
            logger.warning("dictionary_cache_read_failed", dictionary=kind, error_type=type(exc).__name__)

        # Ошибка источника не является ошибкой кэша и должна дойти до вызывающего кода.
        items = await self._repository.list_items(kind)
        payload = _adapter.dump_json(items).decode("utf-8")
        try:
            await self._cache.write(key, payload, self._ttl)
        except RedisError as exc:
            logger.warning("dictionary_cache_write_failed", dictionary=kind, error_type=type(exc).__name__)
        return items
