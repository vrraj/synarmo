from __future__ import annotations

from pathlib import Path

from synarmo.autocomplete_eval import AutocompleteEvaluation, evaluate_with_llama
from synarmo.models.base import GenerationOptions


class LlamaCppBackend:
    name = "llama-cpp"

    def __init__(
        self,
        model_path: Path | None,
        *,
        model_repo_id: str | None = None,
        model_filename: str | None = None,
        models_cache_dir: Path | None = None,
        n_ctx: int = 2048,
    ) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Install with: pip install synarmo[llama]"
            ) from exc

        if model_repo_id:
            if not model_filename:
                raise ValueError("SYNARMO_MODEL is required when SYNARMO_MODEL_REPO_ID is set")
            self._llm = Llama.from_pretrained(
                repo_id=model_repo_id,
                filename=model_filename,
                local_dir=str(models_cache_dir) if models_cache_dir else None,
                n_ctx=n_ctx,
                logits_all=True,
                verbose=False,
            )
            return

        if model_path is None:
            raise ValueError("model_path is required for the llama-cpp backend")
        if not model_path.exists():
            raise FileNotFoundError(f"GGUF model not found: {model_path}")

        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            logits_all=True,
            verbose=False,
        )

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        result = self._llm(
            prompt,
            max_tokens=options.max_tokens,
            temperature=options.temperature,
            top_p=options.top_p,
            stop=options.stop or None,
        )
        return str(result["choices"][0]["text"])

    def evaluate_autocomplete(
        self,
        *,
        context: str,
        typed_text: str,
        choices: int = 3,
        max_tokens: int = 10,
        max_words: int = 1,
        temperature: float = 0.5,
        top_p: float = 0.95,
        logprob_pool: int = 12,
    ) -> AutocompleteEvaluation:
        return evaluate_with_llama(
            self._llm,
            context=context,
            typed_text=typed_text,
            choices=choices,
            max_tokens=max_tokens,
            max_words=max_words,
            temperature=temperature,
            top_p=top_p,
            logprob_pool=logprob_pool,
        )
