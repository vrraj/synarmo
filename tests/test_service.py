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


def test_health_endpoint_reports_runtime_diagnostics() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(SynarmoEngine.load(profile="service-health-test", n_gpu_layers=0))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["backend"] == "mock"
    assert response.json()["n_gpu_layers"] == 0


def test_autocomplete_evaluation_endpoint_accepts_json_body() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-eval-test"))
    schema = app.openapi()

    eval_schema = schema["paths"]["/evaluate/autocomplete"]["post"]
    assert "requestBody" in eval_schema
    parameter_names = [item["name"] for item in eval_schema.get("parameters", [])]
    assert "request" not in parameter_names


def test_ui_endpoints_render_static_assets() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(SynarmoEngine.load(profile="service-ui-test"))
    paths = {route.path for route in app.routes}

    assert "/" in paths
    assert "/ui" in paths
    assert "/static" in paths

    client = TestClient(app)
    response = client.get("/ui")

    assert response.status_code == 200
    assert "/static/css/synarmo.css" in response.text
    assert "/static/js/synarmo.js" in response.text
    assert "gpu-layers-value" in response.text
    assert "continuation-temperature" in response.text
    assert "continuation-top-p" in response.text
    assert "continuation-top-k" not in response.text
    assert "<style>" not in response.text
    assert "<script>" not in response.text

    assert client.get("/static/css/synarmo.css").status_code == 200
    assert client.get("/static/js/synarmo.js").status_code == 200


def test_ui_defaults_render_from_env(monkeypatch) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    monkeypatch.setenv("SYNARMO_MAX_SUGGESTIONS", "4")
    monkeypatch.setenv("SYNARMO_MAX_TOKENS", "7")
    monkeypatch.setenv("SYNARMO_MAX_SUGGESTION_WORDS", "2")
    monkeypatch.setenv("SYNARMO_TEMPERATURE", "0.6")
    monkeypatch.setenv("SYNARMO_TOP_P", "0.85")
    monkeypatch.setenv("SYNARMO_CONTINUATION_TEMPERATURE", "0.5")
    monkeypatch.setenv("SYNARMO_CONTINUATION_TOP_P", "0.9")
    monkeypatch.setenv("SYNARMO_PHRASE_LOGPROBS", "1")
    monkeypatch.setenv("SYNARMO_LOGPROB_POOL", "18")

    engine = SynarmoEngine.load(profile="service-ui-env-test")
    app = create_app(engine)
    response = TestClient(app).get("/ui")

    assert engine.config.phrase_logprobs is True
    assert response.status_code == 200
    assert 'id="choices" type="number" min="1" max="10" step="1" value="4"' in response.text
    assert 'id="candidate-tokens" type="number" min="1" max="64" step="1" value="7"' in response.text
    assert 'id="candidate-words" type="number" min="1" max="8" step="1" value="2"' in response.text
    assert 'id="temperature" type="number" min="0" max="2" step="0.1" value="0.6" disabled' in response.text
    assert 'id="top-p" type="number" min="0" max="1" step="0.05" value="0.85" disabled' in response.text
    assert (
        'id="continuation-temperature" type="number" min="0" max="2" step="0.1" value="0.5"'
        in response.text
    )
    assert (
        'id="continuation-top-p" type="number" min="0" max="1" step="0.05" value="0.9"'
        in response.text
    )
    assert 'id="logprob-pool" type="number" min="1" max="50" step="1" value="18"' in response.text
