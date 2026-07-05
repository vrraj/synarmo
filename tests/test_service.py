import pytest

from synarmo import SynarmoEngine
from synarmo.service.app import create_app


def test_suggest_endpoint_accepts_json_body() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-test"))
    schema = app.openapi()

    suggest_schema = schema["paths"]["/suggest"]["post"]
    assert "requestBody" in suggest_schema
    parameter_names = [item["name"] for item in suggest_schema.get("parameters", [])]
    assert "request" not in parameter_names


def test_autocomplete_evaluation_endpoint_accepts_json_body() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-eval-test"))
    schema = app.openapi()

    eval_schema = schema["paths"]["/evaluate/autocomplete"]["post"]
    assert "requestBody" in eval_schema
    parameter_names = [item["name"] for item in eval_schema.get("parameters", [])]
    assert "request" not in parameter_names


def test_ui_endpoint_is_registered() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-ui-test"))
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/ui" in paths
