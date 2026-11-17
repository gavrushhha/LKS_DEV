"""Transactional outbox (ТЗ, 8.3). Реализация — T13.1."""

from typing import Any


async def publish(session: Any, event_type: str, subject: str, data: dict[str, Any]) -> None:
    """Записать событие в outbox в той же транзакции, что и данные.

    TODO(T13.1): таблица outbox, релей в брокер, гарантия at-least-once.
    """
    raise NotImplementedError("T13.1")
