"""Пул соединений с репликой БД Тандема (только чтение)."""

from typing import Any

from app.core.config import settings


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

    async def connect(self) -> None:
        """TODO(T2.1): создать пул asyncpg с read-only параметрами."""
        raise NotImplementedError("T2.1")

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """TODO(T2.3): выполнить SELECT и вернуть строки."""
        raise NotImplementedError("T2.3")

    @property
    def mode(self) -> str:
        return settings.tandem_mode

    async def close(self) -> None:
        self._pool = None
