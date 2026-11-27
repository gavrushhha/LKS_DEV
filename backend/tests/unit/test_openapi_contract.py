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


def test_generated_system_schemas_match_contract() -> None:
    contract_path = Path(__file__).resolve().parents[2] / "openapi" / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    actual = app.openapi()
    for path in ("/health", "/ready"):
        expected = contract["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        ref = actual["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
            "$ref"
        ]
        generated = actual["components"]["schemas"][ref.rsplit("/", 1)[-1]]
        for name, prop in expected["properties"].items():
            assert generated["properties"][name]["type"] == prop["type"]
    assert "503" in actual["paths"]["/ready"]["get"]["responses"]
    assert "application/problem+json" in actual["paths"]["/ready"]["get"]["responses"]["503"]["content"]
    expected_problem = contract["components"]["schemas"]["Problem"]
    generated_problem = actual["components"]["schemas"]["Problem"]
    assert set(expected_problem["required"]) == set(generated_problem["required"])
    assert set(expected_problem["properties"]).issubset(generated_problem["properties"])
    for name, prop in expected_problem["properties"].items():
        generated_prop = generated_problem["properties"][name]
        variants = generated_prop.get("anyOf", [generated_prop])
        assert any(variant.get("type") == prop["type"] for variant in variants)
