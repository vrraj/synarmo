from synarmo import SynarmoEngine, predict
from synarmo.autocomplete_eval import AutocompleteCandidate, AutocompleteEvaluation


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


class AutocompleteBackend:
    name = "autocomplete"

    def __init__(self) -> None:
        self.called = False

    def generate(self, prompt, options):  # noqa: ANN001
        raise AssertionError("suggest should use evaluate_autocomplete when available")

    def evaluate_autocomplete(self, **kwargs):  # noqa: ANN003
        self.called = True
        return AutocompleteEvaluation(
            context=kwargs["context"],
            prompt="prompt",
            candidates=[
                AutocompleteCandidate(
                    text="go outside",
                    starter=" go",
                    rest=" outside",
                    logprob=-0.2,
                )
            ],
        )


def test_engine_suggest_uses_autocomplete_evaluator_when_available(tmp_path) -> None:
    from synarmo.config import SynarmoConfig
    from synarmo.memory import UserMemory

    backend = AutocompleteBackend()
    engine = SynarmoEngine(
        config=SynarmoConfig(max_suggestions=1, max_suggestion_words=2, profiles_dir=tmp_path),
        backend=backend,
        memory=UserMemory(profile="test"),
    )

    suggestions = engine.suggest("I want to", context="At home")

    assert backend.called
    assert [item.text for item in suggestions] == ["go outside"]
    assert suggestions[0].source == "autocomplete"
