from synarmo.cli import _compose
from synarmo.engine import SynarmoEngine


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
