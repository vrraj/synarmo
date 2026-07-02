from synarmo.suggestions import SuggestionRanker


def test_ranker_deduplicates_and_limits_to_four_words() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "go outside now please today\n- go outside now please today\nthank you",
        current_text="I want to",
        max_suggestions=4,
    )

    assert [item.text for item in suggestions] == ["thank you", "go outside now please"]


def test_ranker_strips_numbered_list_markers() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "(1) I need to\n[2] have some water\n3. go outside",
        current_text="I want to",
        max_suggestions=4,
    )

    assert {item.text for item in suggestions} == {
        "I need to",
        "go outside",
        "have some water",
    }


def test_ranker_strips_trailing_numbered_markers() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "I need to [2]",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["I need to"]


def test_ranker_drops_placeholder_suggestions() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "[ ]\nhelp me",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["help me"]


def test_ranker_drops_suggestions_already_at_current_tail() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "go outside\nhave water",
        current_text="I want to go outside",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["have water"]
