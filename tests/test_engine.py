from synarmo import SynarmoEngine, predict


def test_engine_returns_short_suggestions() -> None:
    engine = SynarmoEngine.load(profile="test")

    suggestions = engine.suggest("I want to", context="At home")

    assert 1 <= len(suggestions) <= 4
    assert all(1 <= len(item.text.split()) <= 4 for item in suggestions)


def test_predict_convenience_api() -> None:
    suggestions = predict("Can you", context="Asking for help", user_profile="test-api")

    assert suggestions
    assert suggestions[0].text
