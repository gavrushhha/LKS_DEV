"""Сборка зависимостей справочников и закрытие Redis-клиента после запроса."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from app.core.config import settings
from app.core.dictionary_cache import RedisDictionaryCache
from app.repositories.dictionary_repository import DictionaryRepository
from app.services.dictionary_service import DictionaryService
from app.source.mock.dictionaries import MockDictionarySource


async def get_dictionary_service() -> AsyncIterator[DictionaryService]:
    async with Redis.from_url(
        settings.redis_dsn,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
        retry=Retry(NoBackoff(), 0),
    ) as redis:
        yield DictionaryService(
            repository=DictionaryRepository(MockDictionarySource()),
            cache=RedisDictionaryCache(redis),
            ttl=settings.dictionary_cache_ttl_seconds,
        )


DictionaryServiceDep = Annotated[DictionaryService, Depends(get_dictionary_service)]
