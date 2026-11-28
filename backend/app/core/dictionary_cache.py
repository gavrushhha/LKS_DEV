"""Доступ к Redis для справочников."""

from __future__ import annotations

from redis.asyncio import Redis


class RedisDictionaryCache:
    def __init__(self, redis: Redis[str]) -> None:
        self._redis = redis

    async def read(self, key: str) -> str | None:
        value: str | None = await self._redis.get(key)
        return value

    async def write(self, key: str, payload: str, ttl: int) -> None:
        await self._redis.set(key, payload, ex=ttl)
