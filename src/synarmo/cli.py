from __future__ import annotations

import argparse
from pathlib import Path

from synarmo.config import BackendName
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
    suggest_parser.add_argument("--max-suggestions", type=int, default=4)

    serve_parser = subcommands.add_parser("serve", help="Run the local REST/WebSocket service.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--profile", default="default")
    serve_parser.add_argument("--backend", choices=["mock", "llama-cpp"], default="mock")
    serve_parser.add_argument("--model-path", type=Path)
    serve_parser.add_argument("--max-suggestions", type=int, default=4)
    return parser


def app() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "suggest":
        engine = _load_engine(args)
        for item in engine.suggest(text=args.text, context=args.context):
            print(item.text)
        return

    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise SystemExit("Install service extras first: pip install synarmo[service]") from exc

        from synarmo.service.app import create_app

        engine = _load_engine(args)
        uvicorn.run(create_app(engine), host=args.host, port=args.port)


def _load_engine(args: argparse.Namespace) -> SynarmoEngine:
    return SynarmoEngine.load(
        profile=args.profile,
        backend=args.backend,
        model_path=args.model_path,
        max_suggestions=args.max_suggestions,
    )


if __name__ == "__main__":
    app()
