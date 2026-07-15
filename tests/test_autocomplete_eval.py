from synarmo.autocomplete_eval import evaluate_with_llama, extract_top_logprobs


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
        return {"choices": [{"text": " soon"}]}

    result = evaluate_with_llama(
        fake_llama,
        context="At home",
        typed_text="I want to",
        choices=2,
        max_words=2,
    )

    assert [candidate.text for candidate in result.candidates] == ["help soon", "heal soon"]
    assert [token.text for token in result.top_tokens] == [" help", " heal", " eat"]
    assert len(calls) == 3
