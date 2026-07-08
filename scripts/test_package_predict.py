#!/usr/bin/env python3
"""Smoke-test the installed synarmo package through its public predict API."""

from __future__ import annotations

import argparse
from pathlib import Path

import synarmo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call synarmo.predict with configurable suggestion parameters.",
    )
    parser.add_argument("--text", default="I want to", help="User typed text so far.")
    parser.add_argument(
        "--context",
        default="At home, asking for help",
        help="Conversation or situation context.",
    )
    parser.add_argument("--profile", default="package-smoke", help="Local profile name.")
    parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="mock")
    parser.add_argument("--model-path", type=Path, help="Optional GGUF path for llama-cpp.")
    parser.add_argument("--choices", type=int, default=3, help="Number of suggestions to return.")
    parser.add_argument("--max-words", type=int, default=4, help="Maximum words per suggestion.")
    parser.add_argument("--temperature", type=float, default=0.25)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=32)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    load_options: dict[str, object] = {
        "backend": args.backend,
        "max_suggestions": args.choices,
        "max_suggestion_words": args.max_words,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
    }
    if args.model_path is not None:
        load_options["model_path"] = args.model_path

    suggestions = synarmo.predict(
        text=args.text,
        context=args.context,
        user_profile=args.profile,
        **load_options,
    )

    for index, suggestion in enumerate(suggestions, start=1):
        print(f"{index}. {suggestion.text} ({suggestion.score:.2f})")


if __name__ == "__main__":
    main()
