from synarmo.suggestions import SuggestionRanker


def test_ranker_deduplicates_and_limits_to_four_words() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "go outside now please today\n- go outside now please today\nthank you",
        current_text="I want to",
        max_suggestions=4,
    )

    assert [item.text for item in suggestions] == ["thank you", "go outside now please"]
