from __future__ import annotations

from pathlib import Path
from threading import Lock

from synarmo.autocomplete_eval import (
    AutocompleteCandidate,
    AutocompleteEvaluation,
)
from synarmo.config import (
    BackendName,
    SynarmoConfig,
    configured_model_filename,
    configured_model_path,
    configured_model_repo_id,
    load_env_file,
)
from synarmo.context import ContextAssembler
from synarmo.infrastructure import collect_infrastructure_diagnostics
from synarmo.memory import UserMemory
from synarmo.models import GenerationOptions, ModelBackend, create_backend
from synarmo.prompts import PromptBuilder
from synarmo.suggestions import Suggestion, SuggestionRanker


class SynarmoEngine:
    def __init__(
        self,
        config: SynarmoConfig,
        backend: ModelBackend,
        memory: UserMemory,
    ) -> None:
        self.config = config
        self.backend = backend
        self.memory = memory
        self.context_assembler = ContextAssembler(max_chars=config.context_window * 2)
        self.prompt_builder = PromptBuilder()
        self.ranker = SuggestionRanker()
        self._generation_lock = Lock()

    @classmethod
    def load(
        cls,
        *,
        profile: str = "default",
        backend: BackendName = "mock",
        model_path: str | Path | None = None,
        profiles_dir: str | Path = "profiles",
        **overrides: object,
    ) -> "SynarmoEngine":
        load_env_file()
        explicit_model_path = model_path is not None
        config = SynarmoConfig(
            profile=profile,
            backend=backend,
            model_path=configured_model_path(model_path),
            model_repo_id=None if explicit_model_path else configured_model_repo_id(),
            model_filename=configured_model_filename(model_path),
            profiles_dir=Path(profiles_dir),
            **overrides,
        )
        memory = UserMemory.load(config.resolved_profile_dir(), profile)
        model_backend = create_backend(config)
        return cls(config=config, backend=model_backend, memory=memory)

    def model_label(self) -> str:
        if self.config.model_path is not None:
            return str(self.config.model_path)
        if self.config.model_filename is not None:
            return self.config.model_filename
        if self.config.model_repo_id is not None:
            return self.config.model_repo_id
        return ""

    def runtime_diagnostics(self) -> dict[str, object]:
        diagnostics: dict[str, object] = {
            "backend": self.backend.name,
            "model": self.model_label(),
            "context_window": self.config.context_window,
            "n_gpu_layers": self.config.n_gpu_layers,
            "llama_verbose": self.config.llama_verbose,
        }
        backend_diagnostics = getattr(self.backend, "diagnostics", None)
        if callable(backend_diagnostics):
            diagnostics.update(backend_diagnostics())
        if "infrastructure" not in diagnostics:
            diagnostics["infrastructure"] = collect_infrastructure_diagnostics(
                model_path=None,
                kv_cache_tokens_current=None,
                kv_cache_tokens_max=None,
            )
        return diagnostics

    def configure(self, **updates: object) -> None:
        self.config = self.config.copy_with(**updates)
        self.context_assembler = ContextAssembler(max_chars=self.config.context_window * 2)

    def suggest(
        self,
        text: str,
        context: str | None = None,
        *,
        max_suggestions: int | None = None,
        max_tokens: int | None = None,
        max_words: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        continuation_temperature: float | None = None,
        continuation_top_p: float | None = None,
        continuation_top_k: int | None = None,
        phrase_logprobs: bool | None = None,
        logprob_pool: int | None = None,
    ) -> list[Suggestion]:
        """Predict continuations using request overrides without changing engine defaults."""
        choices = self.config.max_suggestions if max_suggestions is None else max_suggestions
        token_limit = self.config.max_tokens if max_tokens is None else max_tokens
        word_limit = self.config.max_suggestion_words if max_words is None else max_words
        sampling_temperature = self.config.temperature if temperature is None else temperature
        sampling_top_p = self.config.top_p if top_p is None else top_p
        continuation_sampling_temperature = (
            self.config.continuation_temperature
            if continuation_temperature is None
            else continuation_temperature
        )
        continuation_sampling_top_p = (
            self.config.continuation_top_p if continuation_top_p is None else continuation_top_p
        )
        continuation_sampling_top_k = (
            self.config.continuation_top_k if continuation_top_k is None else continuation_top_k
        )
        use_phrase_logprobs = self.config.phrase_logprobs if phrase_logprobs is None else phrase_logprobs
        logprob_count = self.config.logprob_pool if logprob_pool is None else logprob_pool
        request_config = self.config.copy_with(
            max_suggestions=choices,
            max_tokens=token_limit,
            max_suggestion_words=word_limit,
            temperature=sampling_temperature,
            top_p=sampling_top_p,
            continuation_temperature=continuation_sampling_temperature,
            continuation_top_p=continuation_sampling_top_p,
            continuation_top_k=continuation_sampling_top_k,
            phrase_logprobs=use_phrase_logprobs,
            logprob_pool=logprob_count,
        )
        choices = request_config.max_suggestions
        token_limit = request_config.max_tokens
        word_limit = request_config.max_suggestion_words
        sampling_temperature = request_config.temperature
        sampling_top_p = request_config.top_p
        continuation_sampling_temperature = request_config.continuation_temperature
        continuation_sampling_top_p = request_config.continuation_top_p
        continuation_sampling_top_k = request_config.continuation_top_k
        use_phrase_logprobs = request_config.phrase_logprobs
        logprob_count = request_config.logprob_pool
        assembled_context = self.context_assembler.assemble(
            text=text,
            context=context,
            memory=self.memory if self.config.style_adaptation else UserMemory(profile=self.config.profile),
        )
        evaluator = getattr(self.backend, "evaluate_autocomplete", None)
        if evaluator is not None:
            with self._generation_lock:
                evaluation = evaluator(
                    context=assembled_context,
                    typed_text=text,
                    choices=choices,
                    max_tokens=token_limit,
                    max_words=word_limit,
                    temperature=sampling_temperature,
                    top_p=sampling_top_p,
                    continuation_temperature=continuation_sampling_temperature,
                    continuation_top_p=continuation_sampling_top_p,
                    continuation_top_k=continuation_sampling_top_k,
                    phrase_logprobs=use_phrase_logprobs,
                    logprob_pool=logprob_count,
                )
            ranked = self.ranker.rank(
                "\n".join(candidate.text for candidate in evaluation.candidates),
                current_text=text,
                max_suggestions=choices,
                max_words=word_limit,
            )
            return [
                Suggestion(
                    text=suggestion.text,
                    score=suggestion.score,
                    source="autocomplete",
                )
                for suggestion in ranked
            ]

        generation_count = min(choices * 3, 10)
        generation_max_tokens = max(token_limit, generation_count * 8)
        prompt = self.prompt_builder.build(
            assembled_context=assembled_context,
            max_suggestions=generation_count,
            max_words=word_limit,
        )
        with self._generation_lock:
            raw = self.backend.generate(
                prompt,
                GenerationOptions(
                    max_tokens=generation_max_tokens,
                    temperature=sampling_temperature,
                    top_p=sampling_top_p,
                    stop=self.config.stop,
                ),
            )
            ranked = self.ranker.rank(
                raw,
                current_text=text,
                max_suggestions=choices,
                max_words=word_limit,
            )
            if len(ranked) < choices:
                fill_count = min((choices - len(ranked)) * 3, 10)
                fill_prompt = (
                    f"{prompt}\n\n"
                    "Continue with additional plain text alternatives.\n"
                    f"Return {fill_count} short lines only.\n"
                    "Alternatives:"
                )
                raw = "\n".join(
                    [
                        raw,
                        self.backend.generate(
                            fill_prompt,
                            GenerationOptions(
                                max_tokens=max(token_limit, fill_count * 8),
                                temperature=min(sampling_temperature + 0.1, 2.0),
                                top_p=sampling_top_p,
                                stop=self.config.stop,
                            ),
                        ),
                    ]
                )
        return self.ranker.rank(
            raw,
            current_text=text,
            max_suggestions=choices,
            max_words=word_limit,
        )

    def evaluate_autocomplete(
        self,
        *,
        text: str,
        contexts: list[str],
        choices: int = 3,
        max_tokens: int = 5,
        max_words: int = 1,
        temperature: float = 0.5,
        top_p: float = 0.95,
        continuation_temperature: float | None = None,
        continuation_top_p: float | None = None,
        continuation_top_k: int | None = None,
        phrase_logprobs: bool | None = None,
        logprob_pool: int = 24,
    ) -> list[AutocompleteEvaluation]:
        # Retained as a compatibility diagnostic adapter. It intentionally delegates
        # to suggest() so every public entry point uses the same prediction path.
        results: list[AutocompleteEvaluation] = []
        for context in contexts:
            assembled_context = self.context_assembler.assemble(
                text=text,
                context=context,
                memory=(
                    self.memory
                    if self.config.style_adaptation
                    else UserMemory(profile=self.config.profile)
                ),
            )
            suggestions = self.suggest(
                text,
                context=context,
                max_suggestions=choices,
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
            results.append(
                AutocompleteEvaluation(
                    context=assembled_context,
                    prompt=self.prompt_builder.build_autocomplete(
                        assembled_context=assembled_context,
                        typed_text=text,
                    ),
                    candidates=[
                        AutocompleteCandidate(
                            text=item.text,
                            starter=item.text.split(maxsplit=1)[0],
                            rest="",
                            logprob=item.score,
                        )
                        for item in suggestions
                    ],
                )
            )
        return results

    def remember_phrase(self, phrase: str) -> None:
        normalized = " ".join(phrase.split())
        if normalized and normalized not in self.memory.common_phrases:
            self.memory.common_phrases.append(normalized)
            self.memory.save(self.config.resolved_profile_dir())


_default_engine: SynarmoEngine | None = None


def predict(
    text: str,
    context: str | None = None,
    user_profile: str = "default",
    **load_options: object,
) -> list[Suggestion]:
    return suggest(text=text, context=context, user_profile=user_profile, **load_options)


def suggest(
    text: str,
    context: str | None = None,
    user_profile: str = "default",
    **load_options: object,
) -> list[Suggestion]:
    global _default_engine
    request_option_names = {
        "max_suggestions",
        "max_tokens",
        "max_words",
        "temperature",
        "top_p",
        "continuation_temperature",
        "continuation_top_p",
        "continuation_top_k",
        "phrase_logprobs",
        "logprob_pool",
    }
    request_options = {
        name: load_options.pop(name)
        for name in tuple(load_options)
        if name in request_option_names
    }
    if "max_suggestion_words" in load_options:
        request_options["max_words"] = load_options.pop("max_suggestion_words")
    if _default_engine is None or _default_engine.config.profile != user_profile or load_options:
        _default_engine = SynarmoEngine.load(profile=user_profile, **load_options)
    return _default_engine.suggest(text=text, context=context, **request_options)
