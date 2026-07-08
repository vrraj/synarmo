from pathlib import Path

from synarmo.config import (
    SynarmoConfig,
    configured_max_suggestions,
    configured_model_filename,
    configured_model_path,
    configured_model_repo_id,
    configured_models_cache,
    load_env_file,
)


def test_load_env_file_sets_model_cache(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LOCAL_MODELS_CACHE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("LOCAL_MODELS_CACHE=~/models/synarmo\n", encoding="utf-8")

    load_env_file(env_file)

    assert configured_models_cache() == Path("~/models/synarmo").expanduser()


def test_configured_model_path_resolves_relative_env_path_from_cache(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_MODELS_CACHE", str(tmp_path / "models"))
    monkeypatch.setenv("SYNARMO_MODEL", "tiny.gguf")

    assert configured_model_path() == tmp_path / "models" / "tiny.gguf"


def test_configured_model_path_supports_legacy_env_path(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_MODEL", raising=False)
    monkeypatch.setenv("LOCAL_MODELS_CACHE", str(tmp_path / "models"))
    monkeypatch.setenv("SYNARMO_MODEL_PATH", "legacy.gguf")

    assert configured_model_path() == tmp_path / "models" / "legacy.gguf"


def test_configured_model_prefers_model_selector_over_legacy_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_MODELS_CACHE", str(tmp_path / "models"))
    monkeypatch.setenv("SYNARMO_MODEL", "selected.gguf")
    monkeypatch.setenv("SYNARMO_MODEL_PATH", "legacy.gguf")

    assert configured_model_path() == tmp_path / "models" / "selected.gguf"


def test_configured_model_filename_reads_selected_model(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_MODEL", "llama-3.2-1b-instruct-q4_k_m.gguf")

    assert configured_model_filename() == "llama-3.2-1b-instruct-q4_k_m.gguf"


def test_configured_model_repo_id_reads_env(monkeypatch) -> None:
    monkeypatch.setenv(
        "SYNARMO_MODEL_REPO_ID",
        "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
    )

    assert configured_model_repo_id() == "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF"


def test_explicit_model_path_overrides_env_model_path(tmp_path, monkeypatch) -> None:
    explicit_model = tmp_path / "override.gguf"
    monkeypatch.setenv("LOCAL_MODELS_CACHE", str(tmp_path / "models"))
    monkeypatch.setenv("SYNARMO_MODEL", "selected.gguf")
    monkeypatch.setenv("SYNARMO_MODEL_PATH", "from-env.gguf")

    assert configured_model_path(explicit_model) == explicit_model


def test_explicit_relative_model_path_stays_relative(monkeypatch) -> None:
    monkeypatch.setenv("LOCAL_MODELS_CACHE", "/tmp/models")
    monkeypatch.setenv("SYNARMO_MODEL_PATH", "from-env.gguf")

    assert configured_model_path("models/local.gguf") == Path("models/local.gguf")


def test_configured_max_suggestions_defaults_to_three(monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_MAX_SUGGESTIONS", raising=False)

    assert configured_max_suggestions() == 3


def test_configured_max_suggestions_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_MAX_SUGGESTIONS", "5")

    assert configured_max_suggestions() == 5


def test_config_validates_sampling_and_word_limit() -> None:
    assert SynarmoConfig(top_p=0.5, max_suggestion_words=2).top_p == 0.5


def test_config_rejects_invalid_top_p() -> None:
    try:
        SynarmoConfig(top_p=0.0)
    except ValueError as exc:
        assert "top_p" in str(exc)
    else:
        raise AssertionError("Expected invalid top_p to raise ValueError")


def test_config_rejects_invalid_suggestion_word_limit() -> None:
    try:
        SynarmoConfig(max_suggestion_words=0)
    except ValueError as exc:
        assert "max_suggestion_words" in str(exc)
    else:
        raise AssertionError("Expected invalid max_suggestion_words to raise ValueError")
