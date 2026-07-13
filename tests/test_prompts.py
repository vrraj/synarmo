from synarmo.prompts import PromptBuilder


def test_prompt_requests_exact_unnumbered_suggestions() -> None:
    prompt = PromptBuilder().build(
        assembled_context="Current typed text: Which",
        max_suggestions=3,
        max_words=6,
    )

    assert "Predict exactly 3 natural continuations" in prompt
    assert "Each continuation must be 1 to 6 words" in prompt
    assert "append directly to the typed text" in prompt
    assert "match its context and style" in prompt
    assert "no labels, numbering, explanation, or reply" in prompt
    assert "Current typed text: Which" in prompt
    assert prompt.endswith("Continuations:")


def test_prompt_word_limit_is_at_least_one() -> None:
    zero_prompt = PromptBuilder().build(
        assembled_context="Current typed text: Which",
        max_suggestions=3,
        max_words=0,
    )
    none_prompt = PromptBuilder().build(
        assembled_context="Current typed text: Which",
        max_suggestions=3,
        max_words=None,
    )

    assert "Each continuation must be 1 to 1 words" in zero_prompt
    assert "Each continuation must be 1 to 1 words" in none_prompt


def test_autocomplete_prompt_uses_the_same_guiding_instruction() -> None:
    prompt = PromptBuilder().build_autocomplete(
        assembled_context="Current context: At home\nCurrent typed text: I want to",
        typed_text="I want to",
    )

    assert prompt.startswith("You are Synarmo, a private communication assistant.")
    assert "Predict only the next words" in prompt
    assert "Current typed text:" not in prompt
    assert prompt.endswith("Message:\nI want to")
