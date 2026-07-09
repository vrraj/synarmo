from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    max_tokens: int = 10,
    max_words: int = 1,
    temperature: float = 0.5,
    top_p: float = 0.95,
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
        if len(starters) >= choices:
            break

    candidates: list[AutocompleteCandidate] = []
    for starter in starters:
        response = llm(
            prompt=prompt + starter.text,
            max_tokens=max(max_tokens - 1, 1),
            temperature=0.0,
            top_p=1.0,
            stop=["\n", ".", "!", "?"],
            echo=False,
        )
        rest = str(response["choices"][0]["text"])
        candidate = normalize_candidate(starter.text + rest, max_words=max_words)
        candidates.append(
            AutocompleteCandidate(
                text=candidate,
                starter=starter.text,
                rest=rest,
                logprob=starter.logprob,
            )
        )

    return AutocompleteEvaluation(
        context=context,
        prompt=prompt,
        candidates=candidates,
        top_tokens=top_tokens,
    )
