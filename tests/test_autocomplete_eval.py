import pytest

from synarmo.autocomplete_eval import (
    build_autocomplete_prompt,
    evaluate_with_llama,
    extract_top_logprobs,
    trim_candidate_with_logprobs,
)


def test_build_autocomplete_prompt_omits_duplicate_current_typed_text_label() -> None:
    prompt = build_autocomplete_prompt(
        "Current context: At the gym\nCurrent typed text: I want to",
        "I want to",
    )

    assert "Current typed text:" not in prompt
    assert prompt.endswith("Message:\nI want to")


def test_build_autocomplete_prompt_keeps_stable_prefix_before_context_and_text() -> None:
    first = build_autocomplete_prompt("Current context: At the gym", "I want")
    second = build_autocomplete_prompt("Current context: At the gym", "I want to")

    assert first.startswith("Continue the message with only the next few words.")
    assert first.split("Message:\n", 1)[0] == second.split("Message:\n", 1)[0]


def test_extract_top_logprobs_returns_empty_dict_for_empty_llama_logprobs() -> None:
    probe = {"choices": [{"logprobs": {"top_logprobs": []}}]}

    assert extract_top_logprobs(probe) == {}


def test_evaluate_with_llama_returns_empty_candidates_when_logprobs_are_missing() -> None:
    calls = []

    def fake_llama(**kwargs):
        calls.append(kwargs)
        return {"choices": [{"text": "", "logprobs": {"top_logprobs": []}}]}

    result = evaluate_with_llama(
        fake_llama,
        context="At home",
        typed_text="I want to",
    )

    assert result.candidates == []
    assert result.top_tokens == []
    assert len(calls) == 1


def test_evaluate_with_llama_uses_ranked_logprob_starters() -> None:
    calls = []

    def fake_llama(**kwargs):
        calls.append(kwargs)
        if kwargs["max_tokens"] == 1:
            return {
                "choices": [
                    {
                        "text": "",
                        "logprobs": {
                            "top_logprobs": [
                                {
                                    " help": -0.2,
                                    " eat": -1.0,
                                    " heal": -0.5,
                                }
                            ]
                        },
                    }
                ]
            }
        return {
            "choices": [
                {
                    "text": " soon",
                    "logprobs": {
                        "tokens": [" soon"],
                        "token_logprobs": [-0.3],
                    },
                }
            ]
        }

    result = evaluate_with_llama(
        fake_llama,
        context="At home",
        typed_text="I want to",
        choices=2,
        max_words=2,
    )

    assert [candidate.text for candidate in result.candidates] == ["help soon", "heal soon"]
    assert [candidate.logprob for candidate in result.candidates] == [-0.2, -0.5]
    assert [token.text for token in result.top_tokens] == [" help", " heal", " eat"]
    assert calls[1]["temperature"] == 0.5
    assert calls[1]["top_p"] == 0.9
    assert calls[1]["top_k"] == 20
    assert "logprobs" not in calls[1]
    assert len(calls) == 3


def test_evaluate_with_llama_can_score_with_phrase_logprobs() -> None:
    calls = []

    def fake_llama(**kwargs):
        calls.append(kwargs)
        if kwargs["max_tokens"] == 1:
            return {
                "choices": [
                    {
                        "text": "",
                        "logprobs": {"top_logprobs": [{" help": -0.2}]},
                    }
                ]
            }
        return {
            "choices": [
                {
                    "text": " soon",
                    "logprobs": {
                        "tokens": [" soon"],
                        "token_logprobs": [-0.6],
                    },
                }
            ]
        }

    result = evaluate_with_llama(
        fake_llama,
        context="At home",
        typed_text="I want to",
        max_words=2,
        phrase_logprobs=True,
    )

    assert calls[1]["logprobs"] == 1
    assert result.candidates[0].text == "help soon"
    assert result.candidates[0].logprob == pytest.approx((-0.2 - 0.6) / 2)


def test_evaluate_with_llama_accepts_continuation_sampling_options() -> None:
    calls = []

    def fake_llama(**kwargs):
        calls.append(kwargs)
        if kwargs["max_tokens"] == 1:
            return {
                "choices": [
                    {
                        "text": "",
                        "logprobs": {"top_logprobs": [{" hello": -0.2}]},
                    }
                ]
            }
        return {
            "choices": [
                {
                    "text": " there",
                    "logprobs": {
                        "tokens": [" there"],
                        "token_logprobs": [-0.6],
                    },
                }
            ]
        }

    evaluate_with_llama(
        fake_llama,
        context="At home",
        typed_text="I want to",
        continuation_temperature=0.7,
        continuation_top_p=0.85,
        continuation_top_k=24,
    )

    assert calls[1]["temperature"] == 0.7
    assert calls[1]["top_p"] == 0.85
    assert calls[1]["top_k"] == 24


def test_trim_candidate_scores_visible_tokens_only() -> None:
    candidate, logprob = trim_candidate_with_logprobs(
        [" Port", "ugal", " and", " Spain", " are"],
        [-0.2, -0.4, -0.6, -3.0, -3.0],
        max_words=2,
    )

    assert candidate == "Portugal and"
    assert logprob == pytest.approx((-0.2 - 0.4 - 0.6) / 3)


def test_trim_candidate_excludes_formatting_punctuation_from_score() -> None:
    candidate, logprob = trim_candidate_with_logprobs(
        [" hello", ",", " friend", "!"],
        [-0.2, -5.0, -0.4, -0.8],
        max_words=3,
    )

    assert candidate == "hello, friend!"
    assert logprob == pytest.approx((-0.2 - 0.4 - 0.8) / 3)


def test_trim_candidate_keeps_meaningful_punctuation_after_word_limit() -> None:
    candidate, logprob = trim_candidate_with_logprobs(
        [" how", " are", " you", "?"],
        [-0.2, -0.3, -0.4, -0.5],
        max_words=3,
    )

    assert candidate == "how are you?"
    assert logprob == pytest.approx((-0.2 - 0.3 - 0.4 - 0.5) / 4)
