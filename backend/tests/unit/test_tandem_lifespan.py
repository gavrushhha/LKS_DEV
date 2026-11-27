"""Тесты модуля tandem_lifespan."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from starlette.requests import Request

from app.core.deps import get_tandem_client
from app.main import lifespan


async def test_lifespan_closes_client_on_shutdown(monkeypatch):
    client = MagicMock()
    client.close = AsyncMock()
    client.connect = AsyncMock()
    monkeypatch.setattr("app.main.TandemClient", lambda: client)
    app = FastAPI()

    async with lifespan(app):
        assert app.state.tandem_client is client
        client.connect.assert_not_awaited()
        client.close.assert_not_awaited()

    client.close.assert_awaited_once()


async def test_lifespan_closes_client_after_error(monkeypatch):
    client = MagicMock()
    client.close = AsyncMock()
    monkeypatch.setattr("app.main.TandemClient", lambda: client)
    with pytest.raises(RuntimeError, match="failure"):
        async with lifespan(FastAPI()):
            raise RuntimeError("failure")
    client.close.assert_awaited_once()


async def test_dependency_connects_shared_client_on_demand(monkeypatch):
    client = MagicMock()
    client.close = AsyncMock()
    client.connect = AsyncMock()
    monkeypatch.setattr("app.main.TandemClient", lambda: client)
    app = FastAPI()
    request = Request({"type": "http", "app": app})

    async with lifespan(app):
        assert await get_tandem_client(request) is client
        assert await get_tandem_client(request) is client
        assert client.connect.await_count == 2
    client.close.assert_awaited_once()
