"""Базовая сверка системных маршрутов с контрактом OpenAPI."""

import json
from pathlib import Path

import yaml

from app.core.errors import problem_response
from app.main import app


def assert_schema_matches(expected, actual, components) -> None:
    if "$ref" in actual:
        actual = components[actual["$ref"].rsplit("/", 1)[-1]]
    if "anyOf" in actual:
        actual = next(option for option in actual["anyOf"] if option.get("type") != "null")
        if "$ref" in actual:
            actual = components[actual["$ref"].rsplit("/", 1)[-1]]
    if "type" in expected:
        assert actual.get("type") == expected["type"]
    for name, prop in expected.get("properties", {}).items():
        assert name in actual.get("properties", {})
        assert_schema_matches(prop, actual["properties"][name], components)
    if "items" in expected:
        assert_schema_matches(expected["items"], actual["items"], components)
    if isinstance(expected.get("additionalProperties"), dict):
        assert_schema_matches(expected["additionalProperties"], actual["additionalProperties"], components)


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
        generated = actual["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        assert_schema_matches(expected, generated, actual["components"]["schemas"])
    assert set(actual["paths"]["/ready"]["get"]["responses"]["200"]["content"]) == {"application/json"}
    assert "503" in actual["paths"]["/ready"]["get"]["responses"]
    assert set(actual["paths"]["/ready"]["get"]["responses"]["503"]["content"]) == {
        "application/problem+json"
    }
    expected_problem = contract["components"]["schemas"]["Problem"]
    generated_problem = actual["components"]["schemas"]["Problem"]
    assert set(expected_problem["required"]) == set(generated_problem["required"])
    assert set(expected_problem["properties"]).issubset(generated_problem["properties"])
    assert_schema_matches(expected_problem, generated_problem, actual["components"]["schemas"])
