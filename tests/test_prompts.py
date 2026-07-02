from synarmo.prompts import PromptBuilder


def test_prompt_requests_exact_unnumbered_suggestions() -> None:
    prompt = PromptBuilder().build(assembled_context="Current text: I want to", max_suggestions=3)

    assert "Suggest exactly 3" in prompt
    assert "Do not number or label suggestions." in prompt
    assert "Do not use brackets, placeholders, or empty choices." in prompt
