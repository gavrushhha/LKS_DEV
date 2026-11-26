from unittest.mock import AsyncMock, Mock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.lks_db import get_lks_session
from app.main import app


@pytest.mark.parametrize("has_scales", [True, False])
async def test_grading_scales_response(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    has_scales: bool,
) -> None:
    scale = {
        "id": "9167180b-d48f-4a43-8c7d-34f1ff25c7ee",
        "name": "Пятибалльная",
        "values": ["2", "3", "4", "5"],
        "pass_value": "3",
        "brs_thresholds": [{"min_points": 75.5, "grade": "4"}],
    }
    rows = [scale] if has_scales else []

    result = Mock()
    result.mappings.return_value = rows
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    monkeypatch.setitem(app.dependency_overrides, get_lks_session, lambda: session)

    response = await client.get("/api/v1/dictionaries/grading-scales")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == rows
    session.execute.assert_awaited_once()