from synarmo.cli import _compose, build_parser
from synarmo.engine import SynarmoEngine


def test_serve_host_defaults_to_loopback() -> None:
    args = build_parser().parse_args(["serve"])

    assert args.host == "127.0.0.1"
    assert args.port == 8765


def test_serve_host_can_bind_all_interfaces() -> None:
    args = build_parser().parse_args(["serve", "--host", "0.0.0.0"])

    assert args.host == "0.0.0.0"


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
