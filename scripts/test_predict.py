#!/usr/bin/env python3
"""Minimal interactive SynarmoEngine compose loop inspired by README usage snippets."""

from __future__ import annotations

import argparse
from pathlib import Path

from synarmo import SynarmoEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Iteratively request suggestions and append them to the typed text.",
    )
    parser.add_argument(
        "--text",
        default="I want to",
        help="Starting text to continue (defaults to the README example).",
    )
    parser.add_argument(
        "--context",
        default="in the gym working out with a coach",
        help="Optional scene or conversation context to steer suggestions.",
    )
    parser.add_argument(
        "--backend",
        choices=["mock", "llama-cpp"],
        default="mock",
        help="Inference backend to load (mock is dependency-free for quick tests).",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        help="Optional GGUF file for the llama-cpp backend.",
    )
    parser.add_argument(
        "--choices",
        type=int,
        default=3,
        help="Number of short suggestions to return.",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=4,
        help="Maximum words to display per suggestion.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=12,
        help="Maximum accepted suggestions before exiting.",
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
        "max_suggestion_words": args.max_words,
    }
    if args.model_path is not None:
        load_options["model_path"] = args.model_path

    engine = SynarmoEngine.load(**load_options)
    typed_text = args.text

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
