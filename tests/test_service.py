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
    assert response.json()["infrastructure"]["kv_cache_tokens_current"] is None


def test_autocomplete_evaluation_endpoint_accepts_json_body() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-eval-test"))
    schema = app.openapi()

    eval_schema = schema["paths"]["/evaluate/autocomplete"]["post"]
    assert "requestBody" in eval_schema
    parameter_names = [item["name"] for item in eval_schema.get("parameters", [])]
    assert "request" not in parameter_names


def test_voice_endpoint_accepts_json_body() -> None:
    pytest.importorskip("fastapi")

    app = create_app(SynarmoEngine.load(profile="service-voice-test"))
    schema = app.openapi()

    assert "requestBody" in schema["paths"]["/voice"]["post"]


def test_context_endpoints_store_reusable_presets(tmp_path) -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    app = create_app(SynarmoEngine.load(profile="service-contexts-test"), contexts_path=tmp_path / "contexts.yaml")
    client = TestClient(app)

    save = client.put(
        "/contexts/Doctor%27s%20office",
        json={"name": "Doctor's office", "text": "Asking for help at an appointment."},
    )

    assert save.status_code == 200
    assert client.get("/contexts").json() == {
        "contexts": [{"name": "Doctor's office", "text": "Asking for help at an appointment."}]
    }


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
    assert "voice-btn" in response.text
    assert "voice-backend" in response.text
    assert "infrastructure-metrics" in response.text
    assert "refresh-infrastructure-btn" in response.text
    assert "<style>" not in response.text
    assert "<script>" not in response.text

    assert client.get("/static/css/synarmo.css").status_code == 200
    assert client.get("/static/js/synarmo.js").status_code == 200
