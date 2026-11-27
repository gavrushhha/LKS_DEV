"""Базовая сверка системных маршрутов с контрактом OpenAPI."""

import json
from pathlib import Path

import yaml

from app.core.errors import problem_response
from app.main import app


def test_system_routes_match_contract() -> None:
    contract_path = Path(__file__).resolve().parents[2] / "openapi" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    actual = app.openapi()
    for path in ("/health", "/ready"):
        assert "get" in contract["paths"][path]
        assert "get" in actual["paths"][path]
    assert "/api/v1/ready" not in actual["paths"]


def test_problem_required_fields_match_contract() -> None:
    contract_path = Path(__file__).resolve().parents[2] / "openapi" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    required = contract["components"]["schemas"]["Problem"]["required"]
    response = problem_response(404, "not_found", "Не найдено")
    assert set(required).issubset(json.loads(bytes(response.body)))
