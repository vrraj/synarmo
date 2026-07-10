from __future__ import annotations

from pathlib import Path
from threading import Lock

from synarmo.autocomplete_eval import (
    AutocompleteCandidate,
    AutocompleteEvaluation,
    LogprobToken,
    build_autocomplete_prompt,
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
            "n_gpu_layers": self.config.n_gpu_layers,
            "llama_verbose": self.config.llama_verbose,
        }
        backend_diagnostics = getattr(self.backend, "diagnostics", None)
        if callable(backend_diagnostics):
            diagnostics.update(backend_diagnostics())
        return diagnostics

    def configure(self, **updates: object) -> None:
        self.config = self.config.copy_with(**updates)
        self.context_assembler = ContextAssembler(max_chars=self.config.context_window * 2)

    def suggest(self, text: str, context: str | None = None) -> list[Suggestion]:
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
                    choices=self.config.max_suggestions,
                    max_tokens=self.config.max_tokens,
                    max_words=self.config.max_suggestion_words,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    logprob_pool=self.config.logprob_pool,
                )
            seen: set[str] = set()
            suggestions: list[Suggestion] = []
            for candidate in evaluation.candidates:
                normalized = candidate.text.strip()
                key = normalized.lower()
                if not normalized or key in seen:
                    continue
                seen.add(key)
                suggestions.append(
                    Suggestion(
                        text=normalized,
                        score=candidate.logprob,
                        source="autocomplete",
                    )
                )
            return suggestions

        generation_count = min(self.config.max_suggestions * 3, 10)
        generation_max_tokens = max(self.config.max_tokens, generation_count * 8)
        prompt = self.prompt_builder.build(
            assembled_context=assembled_context,
            max_suggestions=generation_count,
            max_words=self.config.max_suggestion_words,
        )
        with self._generation_lock:
            raw = self.backend.generate(
                prompt,
                GenerationOptions(
                    max_tokens=generation_max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    stop=self.config.stop,
                ),
            )
            ranked = self.ranker.rank(
                raw,
                current_text=text,
                max_suggestions=self.config.max_suggestions,
                max_words=self.config.max_suggestion_words,
            )
            if len(ranked) < self.config.max_suggestions:
                fill_count = min((self.config.max_suggestions - len(ranked)) * 3, 10)
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
                                max_tokens=max(self.config.max_tokens, fill_count * 8),
                                temperature=min(self.config.temperature + 0.1, 2.0),
                                top_p=self.config.top_p,
                                stop=self.config.stop,
                            ),
                        ),
                    ]
                )
        return self.ranker.rank(
            raw,
            current_text=text,
            max_suggestions=self.config.max_suggestions,
            max_words=self.config.max_suggestion_words,
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
        logprob_pool: int = 24,
    ) -> list[AutocompleteEvaluation]:
        evaluator = getattr(self.backend, "evaluate_autocomplete", None)
        if evaluator is None:
            return [
                AutocompleteEvaluation(
                    context=context,
                    prompt=build_autocomplete_prompt(context, text),
                    candidates=[
                        AutocompleteCandidate(
                            text=f"suggestion {index}",
                            starter=f"suggestion {index}",
                            rest="",
                            logprob=0.0,
                        )
                        for index in range(1, choices + 1)
                    ],
                    top_tokens=[
                        LogprobToken(text=f"suggestion {index}", logprob=0.0)
                        for index in range(1, choices + 1)
                    ],
                )
                for context in contexts
            ]

        with self._generation_lock:
            return [
                evaluator(
                    context=context,
                    typed_text=text,
                    choices=choices,
                    max_tokens=max_tokens,
                    max_words=max_words,
                    temperature=temperature,
                    top_p=top_p,
                    logprob_pool=logprob_pool,
                )
                for context in contexts
            ]

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
    if _default_engine is None or _default_engine.config.profile != user_profile or load_options:
        _default_engine = SynarmoEngine.load(profile=user_profile, **load_options)
    return _default_engine.suggest(text=text, context=context)
