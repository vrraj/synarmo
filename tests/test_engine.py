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


def test_predict_accepts_generation_parameters() -> None:
    suggestions = predict(
        "I want to",
        context="At home",
        user_profile="test-api-params",
        max_suggestions=2,
        max_suggestion_words=2,
        temperature=0.4,
        top_p=0.8,
        max_tokens=16,
    )

    assert len(suggestions) == 2
    assert all(len(item.text.split()) <= 2 for item in suggestions)


def test_predict_reloads_when_generation_parameters_change() -> None:
    first = predict(
        "I want to",
        context="At home",
        user_profile="test-api-reload",
        max_suggestions=1,
    )
    second = predict(
        "I want to",
        context="At home",
        user_profile="test-api-reload",
        max_suggestions=2,
    )

    assert len(first) == 1
    assert len(second) == 2
