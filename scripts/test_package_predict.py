#!/usr/bin/env python3
"""Interactive compose loop that exercises the installed synarmo package."""

from __future__ import annotations

import argparse
from pathlib import Path

import synarmo
from synarmo.config import (
    configured_logprob_pool,
    configured_max_suggestion_words,
    configured_max_suggestions,
    configured_max_tokens,
    configured_temperature,
    configured_top_p,
    load_env_file,
)


def build_parser() -> argparse.ArgumentParser:
    load_env_file()
    parser = argparse.ArgumentParser(
        description="Iteratively request suggestions using compose defaults from .env.",
    )
    parser.add_argument("--text", default="I want to", help="Starting text to continue.")
    parser.add_argument(
        "--context",
        default="At the gym, with my coach. Discussing strength training and endurance goals like running up a flight of stairs.",
        help="Conversation or situation context.",
    )
    parser.add_argument("--profile", default="package-smoke", help="Local profile name.")
    parser.add_argument(
        "--backend",
        choices=["mock", "llama-cpp"],
        default="llama-cpp",
        help="Inference backend to load (defaults to llama-cpp for real-model testing).",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        help="Optional GGUF path for llama-cpp. Defaults to SYNARMO_MODEL(_PATH) from .env.",
    )
    parser.add_argument(
        "--choices",
        type=int,
        default=configured_max_suggestions(),
        help="Number of short suggestions to request.",
    )
    parser.add_argument(
        "--candidate-tokens",
        type=int,
        default=configured_max_tokens(),
        help="Maximum tokens to generate per candidate (Compose > candidate tokens).",
    )
    parser.add_argument(
        "--candidate-words",
        type=int,
        default=configured_max_suggestion_words(),
        help="Maximum words per suggestion (Compose > candidate words).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=configured_temperature(),
        help="Sampling temperature used by the backend.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=configured_top_p(),
        help="Top-p nucleus sampling value.",
    )
    parser.add_argument(
        "--logprob-pool",
        type=int,
        default=configured_logprob_pool(),
        help="Number of autocomplete tokens to keep for ranking diagnostics.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=12,
        help="Maximum accepted suggestions before stopping.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically accept the first suggestion each step.",
    )
    return parser


def choose_candidate(candidates: list[str], *, auto: bool) -> str | None:
    if not candidates:
        print("No suggestions available. Stopping.")
        return None

    print("Candidates:")
    for idx, candidate in enumerate(candidates, start=1):
        print(f"  {idx}. {candidate}")

    if auto:
        print("Auto-selected: 1")
        return candidates[0]

    while True:
        choice = input(
            f"Pick 1-{len(candidates)}, Enter for 1, q to stop, or type your own text: "
        ).strip()
        if choice == "":
            return candidates[0]
        lowered = choice.lower()
        if lowered in {"q", "quit", "exit"}:
            return None
        if choice.isdigit():
            as_int = int(choice)
            if 1 <= as_int <= len(candidates):
                return candidates[as_int - 1]
            print("Please choose a valid candidate number.")
            continue
        return choice


def append_text(current: str, addition: str) -> str:
    if not addition:
        return current
    if not current:
        return addition
    if current.endswith(tuple(" \n\t")):
        return current + addition
    if addition[0] in "',.;:!?":
        return current + addition
    return current + " " + addition


def main() -> None:
    args = build_parser().parse_args()

    load_options: dict[str, object] = {
        "backend": args.backend,
        "max_suggestions": args.choices,
        "max_tokens": args.candidate_tokens,
        "max_suggestion_words": args.candidate_words,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "logprob_pool": args.logprob_pool,
    }
    if args.model_path is not None:
        load_options["model_path"] = args.model_path

    engine = synarmo.SynarmoEngine.load(profile=args.profile, **load_options)
    typed_text = args.text

    print("Backend:", engine.config.backend)
    print("Model:", engine.model_label() or "(default)")
    print("Context:", args.context or "(none)")
    print("Starting text:", typed_text)

    for step in range(1, args.max_steps + 1):
        print(f"\n--- Step {step}/{args.max_steps} ---")
        suggestions = engine.suggest(text=typed_text, context=args.context)
        candidates = [suggestion.text for suggestion in suggestions]
        selected = choose_candidate(candidates, auto=args.auto)
        if selected is None:
            break
        typed_text = append_text(typed_text, selected)
        print("Updated text:", typed_text)

    print("\nFinal text:", typed_text)


if __name__ == "__main__":
    main()
