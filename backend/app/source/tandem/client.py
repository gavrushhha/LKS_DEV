"""Пул соединений с репликой БД Тандема (только чтение)."""

import asyncio
from collections import deque
from time import monotonic
from typing import Any

import asyncpg  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_requests: deque[float] = deque()


class TandemClient:
    """Тонкая обёртка над asyncpg-пулом. Реализация — T2.1.

    Требования (ТЗ, 2.2):
      * отдельный пользователь БД только с правами SELECT;
      * пул не более TANDEM_POOL_MAX соединений;
      * statement_timeout = TANDEM_STATEMENT_TIMEOUT_MS;
      * бюджет запросов не более TANDEM_BUDGET_RPM в минуту (учёт в метрике).
    """

    def __init__(self) -> None:
        self._pool: Any | None = None
        self._lifecycle_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Создать отдельный пул для чтения данных источника."""
        async with self._lifecycle_lock:
            if self._pool is None:
                await self._open_pool()

    async def _open_pool(self) -> None:
        """Проверить настройки и создать пул под блокировкой жизненного цикла."""
        if not settings.tandem_db_dsn:
            raise ValueError("TANDEM_DB_DSN не задан")
        if not 0 <= settings.tandem_pool_min <= settings.tandem_pool_max <= 10:
            raise ValueError("Размер пула Тандема должен быть от 0 до 10")
        if settings.tandem_pool_max < 1 or not 0 < settings.tandem_statement_timeout_ms <= 5000:
            raise ValueError("Некорректные настройки пула или таймаута")
        self._pool = await asyncpg.create_pool(
            dsn=settings.tandem_db_dsn,
            min_size=settings.tandem_pool_min,
            max_size=settings.tandem_pool_max,
            timeout=2,
            server_settings={
                "default_transaction_read_only": "on",
                "default_transaction_isolation": "read committed",
                "statement_timeout": str(settings.tandem_statement_timeout_ms),
            },
        )

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Выполнить запрос в транзакции только для чтения."""
        if self._pool is None:
            raise RuntimeError("Пул Тандема не подключён")
        now = monotonic()
        while _requests and _requests[0] <= now - 60:
            _requests.popleft()
        _requests.append(now)
        if len(_requests) > settings.tandem_budget_rpm:
            logger.warning("tandem_query_budget_exceeded", count=len(_requests))
        async with self._pool.acquire(timeout=2) as connection:
            async with connection.transaction(isolation="read_committed", readonly=True):
                rows = await connection.fetch(
                    query, *args, timeout=settings.tandem_statement_timeout_ms / 1000
                )
        return [dict(row) for row in rows]

    @property
    def mode(self) -> str:
        return settings.tandem_mode

    async def close(self) -> None:
        async with self._lifecycle_lock:
            if self._pool is not None:
                pool = self._pool
                await pool.close()
                self._pool = None
