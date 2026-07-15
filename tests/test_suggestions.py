from synarmo.suggestions import SuggestionRanker


def test_ranker_deduplicates_and_limits_to_four_words() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "go outside now please today\n- go outside now please today\nthank you",
        current_text="I want to",
        max_suggestions=4,
    )

    assert [item.text for item in suggestions] == ["thank you", "go outside now please"]


def test_ranker_respects_configured_word_limit() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "go outside now please today",
        current_text="I want to",
        max_suggestions=1,
        max_words=2,
    )

    assert [item.text for item in suggestions] == ["go outside"]


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


def test_ranker_splits_inline_numbered_list_markers() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "1. I need help 2. take a walk 3. have lunch",
        current_text="I want to",
        max_suggestions=4,
    )

    assert {item.text for item in suggestions} == {
        "I need help",
        "take a walk",
        "have lunch",
    }


def test_ranker_strips_trailing_numbered_markers() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "I need to [2]",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["I need to"]


def test_ranker_strips_trailing_inline_number_marker() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "I need help 2.",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["I need help"]


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


def test_ranker_drops_suggestions_already_in_current_text() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "have water\ntake a walk",
        current_text="I want to have water go outside",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["take a walk"]


def test_ranker_drops_instruction_echoes() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "need 3 more different\nI need help",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["I need help"]


def test_ranker_drops_answer_labels_and_splits_commas() -> None:
    ranker = SuggestionRanker()

    suggestions = ranker.rank(
        "Answer:\nhave fun, go to",
        current_text="I want to",
        max_suggestions=3,
    )

    assert [item.text for item in suggestions] == ["have fun", "go to"]
