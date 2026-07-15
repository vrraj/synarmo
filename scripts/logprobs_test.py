#!/usr/bin/env python3
# Run with: uv run python scripts/logprobs_test.py
"""Interactively compare llama.cpp next-token logprobs with sampler settings.

For every step the script calls the model twice with the exact same prompt:
once leaving ``temperature`` and ``top_p`` out of the call, then once passing
the values selected in the session.  It prints the leading logprob entries
from both calls and offers the three leading distinct next words from the
configured call for the next step.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from synarmo.autocomplete_eval import build_autocomplete_prompt  # noqa: E402
from synarmo.config import load_env_file  # noqa: E402


DEFAULT_MODEL = "Llama-3.2-1B.Q4_K_M.gguf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare next-token logprobs with omitted and explicit sampler settings."
    )
    parser.add_argument("--model-path", type=Path, help="Path to the GGUF model.")
    parser.add_argument("--context", default="", help="Context supplied before the typed text.")
    parser.add_argument("--typed", default="", help="Initial text typed by the user.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Initial explicit temperature.")
    parser.add_argument("--top-p", type=float, default=1.0, help="Initial explicit top-p.")
    parser.add_argument("--n-ctx", type=int, default=2048, help="llama.cpp context window.")
    parser.add_argument("--n-threads", type=int, default=4, help="llama.cpp worker threads.")
    parser.add_argument("--max-steps", type=int, default=12, help="Maximum interactive steps.")
    return parser.parse_args()


def resolve_model_path(model_path: Path | None) -> Path:
    if model_path is not None:
        return model_path.expanduser()

    env_model = os.getenv("SYNARMO_MODEL_PATH") or os.getenv("SYNARMO_MODEL")
    if env_model:
        candidate = Path(env_model).expanduser()
        if candidate.is_absolute():
            return candidate
        return Path(os.getenv("LOCAL_MODELS_CACHE", "~/models/synarmo")).expanduser() / candidate

    return Path(os.getenv("LOCAL_MODELS_CACHE", "~/models/synarmo")).expanduser() / DEFAULT_MODEL


def top_logprobs(response: Mapping[str, Any]) -> list[tuple[str, float]]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return []
    logprobs = choices[0].get("logprobs")
    if not isinstance(logprobs, Mapping):
        return []
    tables = logprobs.get("top_logprobs")
    if not isinstance(tables, list) or not tables or not isinstance(tables[0], Mapping):
        return []
    return sorted(
        ((str(token), float(score)) for token, score in tables[0].items()),
        key=lambda entry: entry[1],
        reverse=True,
    )


def print_logprobs(title: str, entries: list[tuple[str, float]]) -> None:
    print(f"\n{title}")
    if not entries:
        print("  No top_logprobs were returned.")
        return
    for index, (token, score) in enumerate(entries[:12], start=1):
        print(f"  {index:2}. {token!r:<22} {score: .6f}")


def distinct_words(entries: list[tuple[str, float]], limit: int = 3) -> list[str]:
    words: list[str] = []
    seen: set[str] = set()
    for token, _ in entries:
        word = token.strip().split(maxsplit=1)[0] if token.strip() else ""
        if not word or word.lower() in seen:
            continue
        seen.add(word.lower())
        words.append(word)
        if len(words) == limit:
            break
    return words


def append_word(typed_text: str, word: str) -> str:
    if not typed_text or typed_text.endswith((" ", "\n", "\t")):
        return typed_text + word
    if word.startswith(("'", ",", ";", ":", ".", "!", "?")):
        return typed_text + word
    return f"{typed_text} {word}"


def update_sampler(temperature: float, top_p: float) -> tuple[float, float] | None:
    response = input(
        f"Sampler: temperature={temperature:g}, top_p={top_p:g}. "
        "Enter to keep, '<temperature> <top-p>' to change, or q to stop: "
    ).strip()
    if response.lower() in {"q", "quit", "exit"}:
        return None
    if not response:
        return temperature, top_p
    try:
        new_temperature, new_top_p = (float(value) for value in response.split())
    except ValueError:
        print("Enter exactly two numbers, for example: 0.6 0.95")
        return update_sampler(temperature, top_p)
    if not 0 <= new_temperature <= 2 or not 0 < new_top_p <= 1:
        print("Temperature must be 0–2 and top-p must be greater than 0 and at most 1.")
        return update_sampler(temperature, top_p)
    return new_temperature, new_top_p


def choose_word(words: list[str]) -> str | None:
    if not words:
        response = input("No word candidates. Type a word to continue or q to stop: ").strip()
        return None if response.lower() in {"q", "quit", "exit"} else response or None
    print("\nNext-word choices (from the explicit-settings call):")
    for index, word in enumerate(words, start=1):
        print(f"  {index}. {word}")
    response = input("Choose 1-3, Enter for 1, type a word, or q to stop: ").strip()
    if response.lower() in {"q", "quit", "exit"}:
        return None
    if not response:
        return words[0]
    if response.isdigit() and 1 <= int(response) <= len(words):
        return words[int(response) - 1]
    return response


def print_word_choices(label: str, entries: list[tuple[str, float]]) -> list[str]:
    words = distinct_words(entries)
    print(f"\n{label}: {', '.join(words) if words else 'None'}")
    return words


def main() -> int:
    args = parse_args()
    load_env_file()
    model_path = resolve_model_path(args.model_path)
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        print("Pass --model-path or set SYNARMO_MODEL_PATH/SYNARMO_MODEL in .env.")
        return 1

    try:
        from llama_cpp import Llama
    except ImportError:
        print("llama-cpp-python is not installed. Try: uv sync --extra llama")
        return 1

    print(f"Loading model: {model_path}")
    print("The omitted-settings call uses llama-cpp-python's own defaults.")
    llm = Llama(
        model_path=str(model_path),
        n_ctx=args.n_ctx,
        n_threads=args.n_threads,
        logits_all=True,
        verbose=False,
    )
    typed_text = args.typed or input("Initial typed text: ").rstrip()
    context = args.context or input("Context (optional): ").rstrip()
    temperature, top_p = args.temperature, args.top_p

    for step in range(1, args.max_steps + 1):
        print(f"\n--- Step {step}/{args.max_steps}: {typed_text!r} ---")
        sampler = update_sampler(temperature, top_p)
        if sampler is None:
            break
        temperature, top_p = sampler
        prompt = build_autocomplete_prompt(context, typed_text)

        omitted = llm(prompt=prompt, max_tokens=1, logprobs=12, echo=False)
        explicit = llm(
            prompt=prompt,
            max_tokens=1,
            temperature=temperature,
            top_p=top_p,
            logprobs=12,
            echo=False,
        )
        omitted_entries = top_logprobs(omitted)
        print_logprobs("Top 12 with temperature/top-p omitted:", omitted_entries)
        explicit_entries = top_logprobs(explicit)
        print_logprobs(
            f"Top 12 with temperature={temperature:g}, top_p={top_p:g}:", explicit_entries
        )
        print_word_choices("Next-word choices with temperature/top-p omitted", omitted_entries)
        words = print_word_choices(
            f"Next-word choices with temperature={temperature:g}, top_p={top_p:g}",
            explicit_entries,
        )

        word = choose_word(words)
        if word is None:
            break
        typed_text = append_word(typed_text, word)

    print(f"\nFinal typed text: {typed_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
