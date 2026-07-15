from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from synarmo.suggestions import Suggestion, SuggestionRanker

PURE_FORMATTING_PUNCTUATION = set(",.;:()[]{}\"'-")
PURE_FORMATTING_PUNCTUATION.update({"-", "–", "—"})


@dataclass(frozen=True, slots=True)
class LogprobToken:
    text: str
    logprob: float


@dataclass(frozen=True, slots=True)
class AutocompleteCandidate:
    text: str
    starter: str
    rest: str
    logprob: float


@dataclass(frozen=True, slots=True)
class AutocompleteEvaluation:
    context: str
    prompt: str
    candidates: list[AutocompleteCandidate]
    top_tokens: list[LogprobToken] = field(default_factory=list)


def build_autocomplete_prompt(context: str, typed_text: str) -> str:
    """Build the v0.1.0 Base-model next-token prompt exactly."""
    return f"""{context.rstrip()}

Live message:
{typed_text}"""


def normalize_candidate(text: str, *, max_words: int) -> str:
    candidate = text.replace("\r", "").replace("\n", " ").strip()
    candidate = candidate.removeprefix(":").strip()
    candidate = candidate.strip("\"'` ")
    words = candidate.split()
    if max_words > 0:
        words = words[:max_words]
    return " ".join(words).strip(" ,;:")


def is_pure_formatting_token(token_text: str) -> bool:
    stripped = token_text.strip()
    return stripped != "" and all(char in PURE_FORMATTING_PUNCTUATION for char in stripped)


def extract_generated_token_logprob_pairs(response: dict[str, Any]) -> list[tuple[str, float]]:
    choices = response.get("choices")
    if not choices:
        return []

    logprobs = choices[0].get("logprobs")
    if not logprobs:
        return []

    raw_token_logprobs = logprobs.get("token_logprobs")
    if not isinstance(raw_token_logprobs, list):
        return []

    raw_tokens = logprobs.get("tokens")
    if not isinstance(raw_tokens, list):
        return []

    pairs: list[tuple[str, float]] = []
    for token, logprob in zip(raw_tokens, raw_token_logprobs):
        if isinstance(logprob, (int, float)) and math.isfinite(float(logprob)):
            pairs.append((str(token), float(logprob)))
    return pairs


def trim_candidate_with_logprobs(
    token_texts: list[str],
    token_logprobs: list[float],
    *,
    max_words: int,
) -> tuple[str, float]:
    consumed_texts: list[str] = []
    consumed_logprobs: list[float] = []

    for token_text, token_logprob in zip(token_texts, token_logprobs):
        previous_candidate = normalize_candidate("".join(consumed_texts), max_words=max_words)
        next_texts = [*consumed_texts, token_text]
        next_candidate = normalize_candidate("".join(next_texts), max_words=max_words)
        if next_candidate == previous_candidate and not is_pure_formatting_token(token_text):
            break
        consumed_texts = next_texts
        consumed_logprobs.append(token_logprob)

    candidate = normalize_candidate("".join(consumed_texts), max_words=max_words)
    scored_logprobs = [
        logprob
        for token_text, logprob in zip(consumed_texts, consumed_logprobs)
        if not is_pure_formatting_token(token_text)
    ]
    if not scored_logprobs:
        scored_logprobs = consumed_logprobs
    if not scored_logprobs:
        return candidate, 0.0
    return candidate, sum(scored_logprobs) / len(scored_logprobs)


def extract_top_logprobs(probe: dict[str, Any]) -> dict[str, float]:
    choices = probe.get("choices")
    if not choices:
        return {}

    logprobs = choices[0].get("logprobs")
    if not logprobs:
        return {}

    top_logprobs = logprobs.get("top_logprobs")
    if not top_logprobs:
        return {}

    raw_top_logprobs = top_logprobs[0]
    if not isinstance(raw_top_logprobs, dict):
        return {}

    return raw_top_logprobs


def evaluate_with_llama(
    llm: Any,
    *,
    context: str,
    typed_text: str,
    choices: int = 3,
    max_tokens: int = 5,
    max_words: int = 1,
    temperature: float = 0.5,
    top_p: float = 0.95,
    continuation_temperature: float = 0.5,
    continuation_top_p: float = 0.9,
    continuation_top_k: int = 20,
    phrase_logprobs: bool = False,
    logprob_pool: int = 24,
) -> AutocompleteEvaluation:
    prompt = build_autocomplete_prompt(context, typed_text)
    probe = llm(
        prompt=prompt,
        max_tokens=1,
        temperature=temperature,
        top_p=top_p,
        logprobs=logprob_pool,
        echo=False,
    )
    raw_top_logprobs = extract_top_logprobs(probe)
    ranked = sorted(raw_top_logprobs.items(), key=lambda item: item[1], reverse=True)
    top_tokens = [LogprobToken(text=text, logprob=float(logprob)) for text, logprob in ranked]

    seen_words: set[str] = set()
    starters: list[LogprobToken] = []
    for token_text, logprob in ranked:
        stripped = token_text.strip()
        if not stripped:
            continue
        first_word = stripped.split()[0].lower()
        if first_word in seen_words:
            continue
        seen_words.add(first_word)
        starters.append(LogprobToken(text=token_text, logprob=float(logprob)))

    ranker = SuggestionRanker()
    candidates: list[AutocompleteCandidate] = []
    for starter in starters:
        continuation_options: dict[str, Any] = {
            "prompt": prompt + starter.text,
            "max_tokens": max(max_tokens - 1, 1),
            "temperature": continuation_temperature,
            "top_p": continuation_top_p,
            "top_k": continuation_top_k,
            "stop": ["\n"],
            "echo": False,
        }
        response = llm(**continuation_options)
        rest = str(response["choices"][0]["text"])
        # Continuation logprobs add material latency. A candidate therefore
        # always retains its starter token's model-provided logprob, regardless
        # of the generated phrase length.
        candidate = normalize_candidate(starter.text + rest, max_words=max_words)
        accepted = ranker.rank_scored(
            [Suggestion(text=candidate, score=starter.logprob, source="autocomplete")],
            current_text=typed_text,
            max_suggestions=1,
            max_words=max_words,
        )
        if not accepted or any(existing.text.lower() == candidate.lower() for existing in candidates):
            continue
        candidates.append(
            AutocompleteCandidate(
                text=candidate,
                starter=starter.text,
                rest=rest,
                logprob=starter.logprob,
            )
        )
        if len(candidates) >= choices:
            break

    return AutocompleteEvaluation(
        context=context,
        prompt=prompt,
        candidates=candidates,
        top_tokens=top_tokens,
    )
