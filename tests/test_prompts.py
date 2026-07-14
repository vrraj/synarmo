from synarmo.prompts import PromptBuilder


def test_base_prompt_contains_only_context_and_final_typed_text() -> None:
    prompt = PromptBuilder().build(
        assembled_context="Current context: At home\nCurrent typed text: Which",
        typed_text="Which",
        max_suggestions=3,
        max_words=6,
    )

    assert prompt == "Current context: At home\n\nWhich"


def test_base_autocomplete_prompt_ends_exactly_with_typed_text() -> None:
    prompt = PromptBuilder().build_autocomplete(
        assembled_context="Current context: At home\nCurrent typed text: I want to",
        typed_text="I want to",
    )

    assert prompt.startswith("Current context: At home\n\n")
    assert "Current typed text:" not in prompt
    assert prompt.endswith("I want to")


def test_instruct_messages_describe_a_short_continuation() -> None:
    messages = PromptBuilder().build_instruct_messages(
        assembled_context="Current context: At home\nCurrent typed text: I want to",
        typed_text="I want to",
        max_suggestions=3,
        max_words=2,
    )

    assert messages[0]["role"] == "system"
    assert "exactly 3 distinct continuations" in messages[0]["content"]
    assert "1 to 2 words" in messages[0]["content"]
    assert messages[1] == {
        "role": "user",
        "content": "Context:\nCurrent context: At home\n\nTyped text:\nI want to",
    }
