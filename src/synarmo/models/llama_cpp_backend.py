from __future__ import annotations

from pathlib import Path

from synarmo.autocomplete_eval import (
    AutocompleteCandidate,
    AutocompleteEvaluation,
    evaluate_with_llama,
)
from synarmo.infrastructure import collect_infrastructure_diagnostics
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
        n_gpu_layers: int = 0,
        verbose: bool = False,
    ) -> None:
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self.gpu_offload_supported = False
        self._configured_model_path = model_path
        try:
            from llama_cpp import Llama, llama_cpp
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Install with: pip install synarmo[llama]"
            ) from exc
        support_probe = getattr(llama_cpp, "llama_supports_gpu_offload", None)
        if support_probe is not None:
            self.gpu_offload_supported = bool(support_probe())

        if model_path is not None and model_path.exists():
            self._llm = Llama(
                model_path=str(model_path),
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                logits_all=True,
                verbose=verbose,
            )
            return

        if model_repo_id:
            if not model_filename:
                raise ValueError("SYNARMO_MODEL is required when SYNARMO_MODEL_REPO_ID is set")
            self._llm = Llama.from_pretrained(
                repo_id=model_repo_id,
                filename=model_filename,
                local_dir=str(models_cache_dir) if models_cache_dir else None,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                logits_all=True,
                verbose=verbose,
            )
            return

        if model_path is None:
            raise ValueError(
                "No llama.cpp model is configured. Set SYNARMO_MODEL_REPO_ID and "
                "SYNARMO_MODEL in .env for an auto-download, set SYNARMO_MODEL to "
                "a local GGUF filename/path, or pass model_path explicitly."
            )
        if not model_path.exists():
            raise FileNotFoundError(f"GGUF model not found: {model_path}")

        self._llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            logits_all=True,
            verbose=verbose,
        )

    def diagnostics(self) -> dict[str, object]:
        requested_layers: int | str = "all" if self.n_gpu_layers == -1 else self.n_gpu_layers
        diagnostics: dict[str, object] = {
            "n_gpu_layers": self.n_gpu_layers,
            "requested_gpu_layers": requested_layers,
            "gpu_offload_supported": self.gpu_offload_supported,
            "llama_verbose": self.verbose,
        }
        actual_context_window = self._actual_context_window()
        if actual_context_window is not None:
            diagnostics["actual_context_window"] = actual_context_window
        total_layers = self._model_layer_count()
        if total_layers is not None:
            diagnostics["model_layers"] = total_layers
        diagnostics["infrastructure"] = collect_infrastructure_diagnostics(
            model_path=self._model_path(),
            kv_cache_tokens_current=self._current_token_count(),
            kv_cache_tokens_max=actual_context_window,
        )
        diagnostics["infrastructure"]["model_architecture"] = self._model_architecture(
            actual_context_window=actual_context_window,
            total_layers=total_layers,
        )
        return diagnostics

    def _model_path(self) -> Path | None:
        if self._configured_model_path is not None:
            return self._configured_model_path
        value = getattr(self._llm, "model_path", None)
        if value:
            return Path(value)
        return None

    def _current_token_count(self) -> int | None:
        try:
            return int(self._llm.n_tokens)
        except Exception:
            return None

    def _model_architecture(
        self, *, actual_context_window: int | None, total_layers: int | None
    ) -> dict[str, int | str | None]:
        metadata = getattr(self._llm, "metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        architecture = _metadata_text(metadata, "general.architecture")
        prefix = f"{architecture}." if architecture else ""
        return {
            "architecture": architecture,
            "sequence_length": actual_context_window,
            "trained_sequence_length": _metadata_int(metadata, f"{prefix}context_length"),
            "vocabulary_size": self._vocabulary_size(metadata, prefix),
            "hidden_dimension": _metadata_int(metadata, f"{prefix}embedding_length"),
            "attention_heads": _metadata_int(metadata, f"{prefix}attention.head_count"),
            "key_value_attention_heads": _metadata_int(
                metadata, f"{prefix}attention.head_count_kv"
            ),
            "layers": total_layers,
        }

    def _vocabulary_size(self, metadata: dict[object, object], prefix: str) -> int | None:
        try:
            return int(self._llm.n_vocab())
        except Exception:
            return _metadata_int(metadata, f"{prefix}vocab_size")

    def _actual_context_window(self) -> int | None:
        try:
            return int(self._llm.n_ctx())
        except Exception:
            return None

    def _model_layer_count(self) -> int | None:
        try:
            from llama_cpp import llama_cpp

            return int(llama_cpp.llama_model_n_layer(self._llm.model))
        except Exception:
            return None

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
        max_tokens: int = 5,
        max_words: int = 1,
        temperature: float = 0.5,
        top_p: float = 0.95,
        continuation_temperature: float = 0.5,
        continuation_top_p: float = 0.9,
        continuation_top_k: int = 20,
        phrase_logprobs: bool = False,
        logprob_pool: int = 24,
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
            continuation_temperature=continuation_temperature,
            continuation_top_p=continuation_top_p,
            continuation_top_k=continuation_top_k,
            phrase_logprobs=phrase_logprobs,
            logprob_pool=logprob_pool,
        )

    def evaluate_instruct_autocomplete(
        self,
        *,
        messages: list[dict[str, str]],
        context: str,
        choices: int = 3,
        max_tokens: int = 5,
        max_words: int = 1,
        temperature: float = 0.5,
        top_p: float = 0.9,
    ) -> AutocompleteEvaluation:
        """Generate alternatives through the GGUF's native chat template."""
        if not self._has_embedded_chat_template():
            raise ValueError(
                "Instruct mode requires a GGUF with an embedded tokenizer.chat_template; "
                "choose a compatible instruct model or set SYNARMO_MODEL_TYPE=base."
            )
        response = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=max(max_tokens, choices * max_words * 4),
            temperature=temperature,
            top_p=top_p,
            stop=["\n\n"],
        )
        content = response["choices"][0]["message"].get("content", "")
        text = content if isinstance(content, str) else ""
        candidates = [
            AutocompleteCandidate(
                text=line.strip(),
                starter=line.strip().split(maxsplit=1)[0] if line.strip() else "",
                rest="",
                logprob=0.0,
            )
            for line in text.splitlines()
            if line.strip()
        ]
        prompt = "\n".join(f"{message['role']}: {message['content']}" for message in messages)
        return AutocompleteEvaluation(context=context, prompt=prompt, candidates=candidates)

    def _has_embedded_chat_template(self) -> bool:
        metadata = getattr(self._llm, "metadata", {})
        return isinstance(metadata, dict) and any(
            isinstance(key, str) and key.startswith("tokenizer.chat_template")
            for key in metadata
        )


def _metadata_text(metadata: dict[object, object], key: str) -> str | None:
    value = metadata.get(key)
    return str(value) if value is not None else None


def _metadata_int(metadata: dict[object, object], key: str) -> int | None:
    try:
        return int(metadata[key])
    except (KeyError, TypeError, ValueError):
        return None
