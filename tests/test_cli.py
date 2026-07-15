from synarmo.cli import _compose, _setup, build_parser
from synarmo.engine import SynarmoEngine


def test_serve_host_defaults_to_loopback() -> None:
    args = build_parser().parse_args(["serve"])

    assert args.host == "127.0.0.1"
    assert args.port == 8765


def test_serve_host_can_bind_all_interfaces() -> None:
    args = build_parser().parse_args(["serve", "--host", "0.0.0.0"])

    assert args.host == "0.0.0.0"


def test_model_ensure_defaults_to_llama_cpp_backend() -> None:
    args = build_parser().parse_args(["model-ensure"])

    assert args.command == "model-ensure"
    assert args.backend == "llama-cpp"
    assert args.profile == "default"


def test_setup_creates_configuration_without_downloading_a_model(tmp_path, capsys) -> None:
    env_path = tmp_path / ".env"
    args = build_parser().parse_args(["setup", "--env-path", str(env_path), "--skip-model"])

    _setup(args)

    config = env_path.read_text()
    assert "SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF" in config
    assert "SYNARMO_VOICE_BACKEND=browser" in config
    assert "SYNARMO_OPENAI_TTS_MODEL=gpt-4o-mini-tts" in config
    assert "Skipped model download and verification." in capsys.readouterr().out


def test_compose_appends_selected_suggestion_and_predicts_again(monkeypatch, capsys) -> None:
    engine = SynarmoEngine.load(profile="compose-test", max_suggestions=3)
    choices = iter(["1", "q"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(choices))

    _compose(engine, text="I want to", context="At home, asking for help")

    output = capsys.readouterr().out
    assert "1. go outside" in output
    assert "2. have some water" in output
    assert "3. talk to you" in output
    assert "I want to go outside" in output
