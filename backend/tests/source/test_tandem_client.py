"""Тесты модуля tandem_client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from app.source.tandem.client import TandemClient


async def test_concurrent_connect_creates_only_one_pool(monkeypatch):
    from app.source.tandem import client as module

    pool = MagicMock()
    create_pool = AsyncMock(return_value=pool)
    monkeypatch.setattr(module.asyncpg, "create_pool", create_pool)
    monkeypatch.setattr(module.settings, "tandem_db_dsn", SecretStr("postgresql://example/test"))
    client = TandemClient()

    await asyncio.gather(client.connect(), client.connect())

    create_pool.assert_awaited_once()
    options = create_pool.await_args.kwargs
    assert options["timeout"] == 2
    assert options["max_size"] <= 10
    assert options["server_settings"]["default_transaction_read_only"] == "on"
    assert options["server_settings"]["default_transaction_isolation"] == "read committed"


async def test_failed_close_retains_pool_for_retry():
    pool = MagicMock()
    pool.close = AsyncMock(side_effect=[RuntimeError("close failed"), None])
    client = TandemClient()
    client._pool = pool

    with pytest.raises(RuntimeError, match="close failed"):
        await client.close()
    await client.close()

    assert pool.close.await_count == 2
    assert client._pool is None


async def test_fetch_requires_connection():
    with pytest.raises(RuntimeError, match="не подключён"):
        await TandemClient().fetch("SELECT 1")


async def test_fetch_uses_read_only_transaction_and_returns_dicts():
    connection = MagicMock()
    connection.fetch = AsyncMock(return_value=[{"id": 12}])
    transaction = connection.transaction.return_value
    transaction.__aenter__ = AsyncMock()
    transaction.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    acquired = pool.acquire.return_value
    acquired.__aenter__ = AsyncMock(return_value=connection)
    acquired.__aexit__ = AsyncMock(return_value=False)
    client = TandemClient()
    client._pool = pool

    rows = await client.fetch("SELECT $1", 12)

    assert rows == [{"id": 12}]
    pool.acquire.assert_called_once_with(timeout=2)
    connection.transaction.assert_called_once_with(isolation="read_committed", readonly=True)
    connection.fetch.assert_awaited_once_with("SELECT $1", 12, timeout=5)
    transaction.__aexit__.assert_awaited_once()


async def test_connect_rejects_timeout_above_limit(monkeypatch):
    from app.source.tandem import client as module

    monkeypatch.setattr(module.settings, "tandem_db_dsn", SecretStr("postgresql://example/test"))
    monkeypatch.setattr(module.settings, "tandem_statement_timeout_ms", 5001)
    with pytest.raises(ValueError, match="таймаута"):
        await TandemClient().connect()
