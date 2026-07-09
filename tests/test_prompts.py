from synarmo.prompts import PromptBuilder


def test_prompt_requests_exact_unnumbered_suggestions() -> None:
    prompt = PromptBuilder().build(assembled_context="Current typed text: Which", max_suggestions=3)

    assert "Suggest exactly 3" in prompt
    assert "immediately after the current typed text" in prompt
    assert "Suggestions are not answers from the assistant." in prompt
    assert "Only return suggestions that pass that append check." in prompt
    assert "Continue the exact typed text; do not replace it." in prompt
    assert "Do not ignore partial words, question starters, or unfinished phrases." in prompt
    assert "Do not answer the user or produce conversational replies." in prompt
    assert "keep numeric values as digits" in prompt
    assert "Do not number or label suggestions." in prompt
    assert "Do not use brackets, placeholders, or empty choices." in prompt
    assert "Current typed text: Which" in prompt
    assert "dish is spicy" in prompt
    assert "Current typed text: Where" in prompt
    assert "is the restroom" in prompt
    assert "Where is the restroom" in prompt
    assert "Return only the good continuation text" in prompt
