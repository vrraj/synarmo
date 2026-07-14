#!/usr/bin/env python3
"""Interactive autocomplete probe for a local GGUF base model.

This script loads a llama.cpp model once, asks for three short autocomplete
suggestions, lets you pick one, appends it to the current text, and repeats.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from synarmo.autocomplete_eval import evaluate_with_llama


# DEFAULT_CONTEXT = """Setting: A busy, high-end Italian restaurant during dinner rush.
# The head chef is shouting out orders to the line cooks. The kitchen staff uses short,
# urgent commands. They are focused on plates, stations, temperatures, and firing dishes.

# Kitchen Stations:
# grill, saute, pasta, pantry, expo

# Kitchen Logs:
# "Fire the risotto!"
# "Need a temperature check on the ribeye steak!"
# "The guest wants the sauce on the side."
# """

DEFAULT_CONTEXT = """ Hello young lady - should we do Mission Peak from Stanford tomorrow around 6-7 PM in the evening. 7 is fine - think you can make it by then?. . Ok Stanford entrance - let’s do the Stanford trail - horse heaven would be better if we did earlier . See you at 7 at Stanford entrance . Tell  your meeting works that it’s a long weelend go home."""
DEFAULT_TYPED_TEXT = "What "
DEFAULT_MODEL = "Llama-3.2-1B.Q4_K_M.gguf"
# DEFAULT_MODEL = "llama-3.2-1b-instruct-q4_k_m.gguf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe a local GGUF model's iterative autocomplete behavior."
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help=(
            "Path to the GGUF model. Defaults to SYNARMO_MODEL_PATH, SYNARMO_MODEL, "
            "LOCAL_MODELS_CACHE/Llama-3.2-1B.Q4_K_M.gguf, or ./Llama-3.2-1B.Q4_K_M.gguf."
        ),
    )
    parser.add_argument("--context", default=DEFAULT_CONTEXT, help="Scenario/context prompt.")
    parser.add_argument(
        "--typed",
        default=DEFAULT_TYPED_TEXT,
        help="Initial text typed by the user.",
    )
    parser.add_argument(
        "--choices",
        type=int,
        default=3,
        help="Number of autocomplete candidates to request per step.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=12,
        help="Maximum number of accepted autocomplete pieces before stopping.",
    )
    parser.add_argument(
        "--candidate-tokens",
        type=int,
        default=10,
        help="Maximum llama tokens to generate before trimming each candidate.",
    )
    parser.add_argument(
        "--candidate-words",
        type=int,
        default=1,
        help="Maximum words to keep from each candidate before appending.",
    )
    parser.add_argument("--n-ctx", type=int, default=2048, help="llama.cpp context window.")
    parser.add_argument("--n-threads", type=int, default=4, help="llama.cpp worker threads.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.5,
        help="Sampling temperature. Raise slightly if all candidates are identical.",
    )
    parser.add_argument("--top-p", type=float, default=0.95, help="Nucleus sampling cutoff.")
    parser.add_argument(
        "--logprob-pool",
        type=int,
        default=12,
        help=(
            "How many top next-token candidates to inspect via logprobs when picking "
            "distinct starting words. Raise this if --choices distinct words can't be "
            "found (e.g. the model is very confident about one continuation)."
        ),
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Always accept the first candidate without prompting.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print each model forward pass, logprob starters, and raw completions.",
    )
    return parser.parse_args()


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def resolve_model_path(model_path: Path | None) -> Path:
    if model_path is not None:
        return model_path.expanduser()

    env_model = os.getenv("SYNARMO_MODEL_PATH") or os.getenv("SYNARMO_MODEL")
    if env_model:
        candidate = Path(env_model).expanduser()
        if candidate.is_absolute():
            return candidate

        cache_dir = Path(os.getenv("LOCAL_MODELS_CACHE", "~/models/synarmo")).expanduser()
        return cache_dir / candidate

    cache_candidate = Path(os.getenv("LOCAL_MODELS_CACHE", "~/models/synarmo")).expanduser()
    cache_candidate = cache_candidate / DEFAULT_MODEL
    if cache_candidate.exists():
        return cache_candidate

    return Path.cwd() / DEFAULT_MODEL


def model_label(model_path: Path) -> str:
    name = model_path.name.lower()
    if "instruct" in name:
        return "instruct"
    return "base"


def print_debug(evaluation: object) -> None:
    print("\n[debug] Forward pass 1: next-token logprob probe")
    print("[debug] Prompt sent to model:")
    print(evaluation.prompt)

    print("\n[debug] Ranked next-token logprobs:")
    for rank, token in enumerate(evaluation.top_tokens, start=1):
        print(f"[debug]   {rank}. token={token.text!r} logprob={token.logprob:.4f}")

    for index, candidate in enumerate(evaluation.candidates, start=1):
        print(f"\n[debug] Forward pass {index + 1}: complete starter {candidate.starter!r}")
        print("[debug] Prompt sent to model:")
        print(evaluation.prompt + candidate.starter)
        print(f"[debug] Raw rest={candidate.rest!r}")
        print(f"[debug] Candidate={candidate.text!r}")


def append_candidate(typed_text: str, candidate: str) -> str:
    if not candidate:
        return typed_text
    if not typed_text or typed_text.endswith((" ", "\n", "\t")):
        return typed_text + candidate
    if candidate.startswith(("'", ",", ";", ":")):
        return typed_text + candidate
    return typed_text + " " + candidate


def choose_candidate(candidates: list[str], *, auto: bool) -> str | None:
    if not candidates:
        print("No candidates returned.")
        return None

    print("\nCandidates:")
    for index, candidate in enumerate(candidates, start=1):
        print(f"  {index}. {candidate}")

    if auto:
        print("Auto-selected: 1")
        return candidates[0]

    while True:
        choice = input(
            f"Pick 1-{len(candidates)}, Enter for 1, q to stop, or type your own word: "
        ).strip()
        if choice == "":
            return candidates[0]
        if choice.lower() in {"q", "quit", "exit"}:
            return None
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(candidates):
                return candidates[index - 1]
            print("Please choose a listed number, Enter, q, or type your own word.")
            continue
        return choice


def main() -> int:
    args = parse_args()
    load_dotenv()

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

    print(f"Loading {model_label(model_path)} model: {model_path}")
    llm = Llama(
        model_path=str(model_path),
        n_ctx=args.n_ctx,
        n_threads=args.n_threads,
        logits_all=True,  # required for logprobs= to work in create_completion
        verbose=False,
    )

    typed_text = args.typed
    print("\nScenario context:")
    print(args.context.rstrip())
    print("\nStarting text:")
    print(typed_text)

    for step in range(1, args.max_steps + 1):
        print(f"\n--- Step {step}/{args.max_steps} ---")
        print(f"Current Message: {typed_text!r}")

        evaluation = evaluate_with_llama(
            llm,
            context=args.context,
            typed_text=typed_text,
            choices=args.choices,
            max_tokens=args.candidate_tokens,
            max_words=args.candidate_words,
            temperature=args.temperature,
            top_p=args.top_p,
            logprob_pool=args.logprob_pool,
        )
        if args.debug:
            print_debug(evaluation)

        candidates = [candidate.text for candidate in evaluation.candidates]
        selected = choose_candidate(candidates, auto=args.auto)
        if selected is None:
            break

        typed_text = append_candidate(typed_text, selected)
        print(f"Updated Message: {typed_text}")

    print("\nFinal Message:")
    print(typed_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
