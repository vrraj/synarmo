from pathlib import Path

from synarmo.config import (
    SynarmoConfig,
    configured_continuation_temperature,
    configured_continuation_top_k,
    configured_continuation_top_p,
    configured_phrase_logprobs,
    configured_logprob_pool,
    configured_context_window,
    configured_max_suggestions,
    configured_max_suggestion_words,
    configured_max_tokens,
    configured_model_filename,
    configured_model_path,
    configured_model_repo_id,
    configured_models_cache,
    configured_temperature,
    configured_llama_verbose,
    configured_n_gpu_layers,
    configured_top_p,
    load_env_file,
)


def test_load_env_file_sets_model_cache(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LOCAL_MODELS_CACHE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("LOCAL_MODELS_CACHE=~/models/synarmo\n", encoding="utf-8")

    load_env_file(env_file)

    assert configured_models_cache() == Path("~/models/synarmo").expanduser()


def test_load_env_file_supports_inline_comments(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("LOCAL_MODELS_CACHE", raising=False)
    monkeypatch.delenv("SYNARMO_CONTEXT_WINDOW", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LOCAL_MODELS_CACHE=~/models/synarmo # Local GGUF cache",
                "SYNARMO_CONTEXT_WINDOW=4096 # llama.cpp n_ctx",
            ]
        ),
        encoding="utf-8",
    )

    load_env_file(env_file)

    assert configured_models_cache() == Path("~/models/synarmo").expanduser()
    assert configured_context_window() == 4096


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


def test_configured_compose_generation_defaults_read_env(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_MAX_TOKENS", "7")
    monkeypatch.setenv("SYNARMO_MAX_SUGGESTION_WORDS", "2")
    monkeypatch.setenv("SYNARMO_TEMPERATURE", "0.4")
    monkeypatch.setenv("SYNARMO_TOP_P", "0.8")
    monkeypatch.setenv("SYNARMO_CONTINUATION_TEMPERATURE", "0.6")
    monkeypatch.setenv("SYNARMO_CONTINUATION_TOP_P", "0.85")
    monkeypatch.setenv("SYNARMO_CONTINUATION_TOP_K", "32")
    monkeypatch.setenv("SYNARMO_PHRASE_LOGPROBS", "1")
    monkeypatch.setenv("SYNARMO_LOGPROB_POOL", "16")

    assert configured_max_tokens() == 7
    assert configured_max_suggestion_words() == 2
    assert configured_temperature() == 0.4
    assert configured_top_p() == 0.8
    assert configured_continuation_temperature() == 0.6
    assert configured_continuation_top_p() == 0.85
    assert configured_continuation_top_k() == 32
    assert configured_phrase_logprobs() is True
    assert configured_logprob_pool() == 16


def test_configured_phrase_logprobs_defaults_to_false(monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_PHRASE_LOGPROBS", raising=False)

    assert configured_phrase_logprobs() is False


def test_configured_context_window_defaults_to_2048(monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_CONTEXT_WINDOW", raising=False)

    assert configured_context_window() == 2048


def test_configured_context_window_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_CONTEXT_WINDOW", "4096")

    assert configured_context_window() == 4096


def test_configured_n_gpu_layers_defaults_to_cpu(monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_N_GPU_LAYERS", raising=False)

    assert configured_n_gpu_layers() == 0


def test_configured_n_gpu_layers_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_N_GPU_LAYERS", "-1")

    assert configured_n_gpu_layers() == -1


def test_configured_llama_verbose_defaults_to_false(monkeypatch) -> None:
    monkeypatch.delenv("SYNARMO_LLAMA_VERBOSE", raising=False)

    assert configured_llama_verbose() is False


def test_configured_llama_verbose_reads_truthy_env(monkeypatch) -> None:
    monkeypatch.setenv("SYNARMO_LLAMA_VERBOSE", "yes")

    assert configured_llama_verbose() is True


def test_config_validates_sampling_and_word_limit() -> None:
    assert SynarmoConfig(top_p=0.5, max_suggestion_words=2).top_p == 0.5


def test_config_rejects_invalid_top_p() -> None:
    try:
        SynarmoConfig(top_p=0.0)
    except ValueError as exc:
        assert "top_p" in str(exc)
    else:
        raise AssertionError("Expected invalid top_p to raise ValueError")


def test_config_validates_continuation_sampling() -> None:
    config = SynarmoConfig(
        continuation_temperature=0.6,
        continuation_top_p=0.9,
        continuation_top_k=32,
    )

    assert config.continuation_temperature == 0.6
    assert config.continuation_top_p == 0.9
    assert config.continuation_top_k == 32


def test_config_rejects_invalid_continuation_top_p() -> None:
    try:
        SynarmoConfig(continuation_top_p=0.0)
    except ValueError as exc:
        assert "continuation_top_p" in str(exc)
    else:
        raise AssertionError("Expected invalid continuation_top_p to raise ValueError")


def test_config_rejects_invalid_continuation_top_k() -> None:
    try:
        SynarmoConfig(continuation_top_k=-1)
    except ValueError as exc:
        assert "continuation_top_k" in str(exc)
    else:
        raise AssertionError("Expected invalid continuation_top_k to raise ValueError")


def test_config_rejects_invalid_suggestion_word_limit() -> None:
    try:
        SynarmoConfig(max_suggestion_words=0)
    except ValueError as exc:
        assert "max_suggestion_words" in str(exc)
    else:
        raise AssertionError("Expected invalid max_suggestion_words to raise ValueError")


def test_config_rejects_invalid_gpu_layers() -> None:
    try:
        SynarmoConfig(n_gpu_layers=-2)
    except ValueError as exc:
        assert "n_gpu_layers" in str(exc)
    else:
        raise AssertionError("Expected invalid n_gpu_layers to raise ValueError")
