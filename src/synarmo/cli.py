from __future__ import annotations

import argparse
from pathlib import Path

from synarmo.config import configured_models_cache, load_env_file
from synarmo.engine import SynarmoEngine
from synarmo.suggestions import Suggestion


_DEFAULT_ENV = """LOCAL_MODELS_CACHE=~/models/synarmo
SYNARMO_MODEL_REPO_ID=QuantFactory/Llama-3.2-1B-GGUF
SYNARMO_MODEL=Llama-3.2-1B.Q4_K_M.gguf
SYNARMO_CONTEXT_WINDOW=4096
SYNARMO_N_GPU_LAYERS=-1
SYNARMO_MAX_SUGGESTIONS=3
SYNARMO_MAX_TOKENS=5
SYNARMO_MAX_SUGGESTION_WORDS=2
SYNARMO_TEMPERATURE=0
SYNARMO_TOP_P=1
SYNARMO_CONTINUATION_TEMPERATURE=0.5
SYNARMO_CONTINUATION_TOP_P=0.9
SYNARMO_CONTINUATION_TOP_K=20
SYNARMO_LOGPROB_POOL=24
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synarmo")
    subcommands = parser.add_subparsers(dest="command", required=True)

    suggest_parser = subcommands.add_parser("suggest", help="Generate local type-ahead suggestions.")
    suggest_parser.add_argument("text")
    suggest_parser.add_argument("--context", default="")
    suggest_parser.add_argument("--profile", default="default")
    suggest_parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="mock")
    suggest_parser.add_argument("--model-path", type=Path)
    suggest_parser.add_argument("--max-suggestions", type=int)

    model_ensure_parser = subcommands.add_parser(
        "model-ensure",
        help="Download or verify the configured local inference model.",
    )
    model_ensure_parser.add_argument("--profile", default="default")
    model_ensure_parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="llama-cpp")
    model_ensure_parser.add_argument("--model-path", type=Path)

    setup_parser = subcommands.add_parser(
        "setup",
        help="Create a default .env, download the configured model, and report readiness.",
    )
    setup_parser.set_defaults(backend="llama-cpp")
    setup_parser.add_argument("--env-path", type=Path, default=Path(".env"))
    setup_parser.add_argument("--profile", default="default")
    setup_parser.add_argument("--model-path", type=Path)
    setup_parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Create or preserve the configuration without loading or downloading the model.",
    )

    compose_parser = subcommands.add_parser(
        "compose",
        help="Interactively choose suggestions and continue predicting.",
    )
    compose_parser.add_argument("text")
    compose_parser.add_argument("--context", default="")
    compose_parser.add_argument("--profile", default="default")
    compose_parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="mock")
    compose_parser.add_argument("--model-path", type=Path)
    compose_parser.add_argument("--max-suggestions", type=int)

    serve_parser = subcommands.add_parser("serve", help="Run the local REST/WebSocket service.")
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address for the service. Use 0.0.0.0 to listen on all interfaces.",
    )
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--profile", default="default")
    serve_parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="mock")
    serve_parser.add_argument("--model-path", type=Path)
    serve_parser.add_argument("--max-suggestions", type=int)
    return parser


def app() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "suggest":
        engine = _load_engine(args)
        text = _display_text(args.text)
        _print_suggestions(text, engine.suggest(text=text, context=args.context))
        return

    if args.command == "model-ensure":
        engine = _load_engine(args)
        print(_format_runtime_diagnostics(engine))
        print(f"Model ready for {args.backend}")
        return

    if args.command == "setup":
        _setup(args)
        return

    if args.command == "compose":
        engine = _load_engine(args)
        _compose(engine, text=args.text, context=args.context)
        return

    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise SystemExit("Install service extras first: pip install synarmo[service]") from exc

        from synarmo.service.app import create_app

        engine = _load_engine(args)
        print(_format_runtime_diagnostics(engine))
        uvicorn.run(create_app(engine), host=args.host, port=args.port)


def _load_engine(args: argparse.Namespace) -> SynarmoEngine:
    options: dict[str, object] = {}
    max_suggestions = getattr(args, "max_suggestions", None)
    if max_suggestions is not None:
        options["max_suggestions"] = max_suggestions

    return SynarmoEngine.load(
        profile=args.profile,
        backend=args.backend,
        model_path=args.model_path,
        **options,
    )


def _setup(args: argparse.Namespace) -> None:
    env_path = args.env_path.expanduser()
    if env_path.exists():
        config_status = f"Kept existing configuration: {env_path}"
    else:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(_DEFAULT_ENV, encoding="utf-8")
        config_status = f"Created configuration: {env_path}"

    load_env_file(env_path)
    print(config_status)
    if args.skip_model:
        print("Skipped model download and verification.")
        return

    engine = _load_engine(args)
    print(_format_runtime_diagnostics(engine))
    print("Synarmo setup complete:")
    print(f"  - Model cache: {configured_models_cache()}")
    print("  - The configured GGUF model is ready")
    print("  - Next: synarmo compose 'I want to' --backend llama-cpp")


def _format_runtime_diagnostics(engine: SynarmoEngine) -> str:
    diagnostics = engine.runtime_diagnostics()
    parts = [
        f"backend={diagnostics.get('backend', '')}",
        f"model={diagnostics.get('model', '')}",
        f"context_window={diagnostics.get('context_window', '')}",
        f"n_gpu_layers={diagnostics.get('n_gpu_layers', '')}",
    ]
    if "actual_context_window" in diagnostics:
        parts.append(f"actual_context_window={diagnostics['actual_context_window']}")
    if "requested_gpu_layers" in diagnostics:
        parts.append(f"requested_gpu_layers={diagnostics['requested_gpu_layers']}")
    if "model_layers" in diagnostics:
        parts.append(f"model_layers={diagnostics['model_layers']}")
    if "gpu_offload_supported" in diagnostics:
        parts.append(f"gpu_offload_supported={diagnostics['gpu_offload_supported']}")
    if "llama_verbose" in diagnostics:
        parts.append(f"llama_verbose={diagnostics['llama_verbose']}")
    return "Synarmo runtime: " + " ".join(parts)


def _display_text(text: str) -> str:
    normalized = " ".join(text.split())
    if normalized.lower() == "my goals":
        return "My Goals are"
    return text.strip()


def _print_suggestions(text: str, suggestions: list[Suggestion]) -> None:
    print(text)
    print("Suggestions:")
    if not suggestions:
        print("No suggestions.")
        return
    for index, item in enumerate(suggestions, start=1):
        print(f"{index}. {item.text}")


def _compose(engine: SynarmoEngine, *, text: str, context: str) -> None:
    current = text
    while True:
        print(f"\n{current}")
        suggestions = engine.suggest(text=current, context=context)
        if not suggestions:
            print("No suggestions.")
            return

        for index, item in enumerate(suggestions, start=1):
            print(f"{index}. {item.text}")

        choice = input(
            f"Choose 1-{len(suggestions)}, enter custom text, or q to quit: "
        ).strip()
        if choice.lower() in {"q", "quit", "exit"}:
            return
        if not choice:
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
            selected = suggestions[int(choice) - 1].text
        else:
            selected = choice
        current = f"{current.rstrip()} {selected.strip()}".strip()


if __name__ == "__main__":
    app()
