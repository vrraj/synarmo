from __future__ import annotations

from pathlib import Path

from synarmo.models.base import GenerationOptions


class LlamaCppBackend:
    name = "llama-cpp"

    def __init__(self, model_path: Path, *, n_ctx: int = 2048) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Install with: pip install synarmo[llama]"
            ) from exc

        if not model_path.exists():
            raise FileNotFoundError(f"GGUF model not found: {model_path}")

        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            verbose=False,
        )

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        result = self._llm(
            prompt,
            max_tokens=options.max_tokens,
            temperature=options.temperature,
            stop=options.stop or None,
        )
        return str(result["choices"][0]["text"])
