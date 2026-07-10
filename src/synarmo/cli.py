from __future__ import annotations

import argparse
from pathlib import Path

from synarmo.engine import SynarmoEngine


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
        for item in engine.suggest(text=args.text, context=args.context):
            print(item.text)
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
    if args.max_suggestions is not None:
        options["max_suggestions"] = args.max_suggestions

    return SynarmoEngine.load(
        profile=args.profile,
        backend=args.backend,
        model_path=args.model_path,
        **options,
    )


def _format_runtime_diagnostics(engine: SynarmoEngine) -> str:
    diagnostics = engine.runtime_diagnostics()
    parts = [
        f"backend={diagnostics.get('backend', '')}",
        f"model={diagnostics.get('model', '')}",
        f"n_gpu_layers={diagnostics.get('n_gpu_layers', '')}",
    ]
    if "requested_gpu_layers" in diagnostics:
        parts.append(f"requested_gpu_layers={diagnostics['requested_gpu_layers']}")
    if "model_layers" in diagnostics:
        parts.append(f"model_layers={diagnostics['model_layers']}")
    if "gpu_offload_supported" in diagnostics:
        parts.append(f"gpu_offload_supported={diagnostics['gpu_offload_supported']}")
    if "llama_verbose" in diagnostics:
        parts.append(f"llama_verbose={diagnostics['llama_verbose']}")
    return "Synarmo runtime: " + " ".join(parts)


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
