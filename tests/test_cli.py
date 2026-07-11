from synarmo.cli import _compose, _display_text, _print_suggestions, build_parser
from synarmo.engine import SynarmoEngine
from synarmo.suggestions import Suggestion


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


def test_suggest_output_labels_original_text_and_suggestions(capsys) -> None:
    _print_suggestions(
        "My Goals are",
        [
            Suggestion("to build strength", 1.0),
            Suggestion("to run upstairs", 0.95),
            Suggestion("without tiring", 0.9),
        ],
    )

    output = capsys.readouterr().out.splitlines()
    assert output == [
        "My Goals are",
        "Suggestions:",
        "1. to build strength",
        "2. to run upstairs",
        "3. without tiring",
    ]


def test_suggest_display_text_completes_my_goals_heading() -> None:
    assert _display_text("My goals") == "My Goals are"


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
