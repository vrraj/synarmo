from __future__ import annotations

from pathlib import Path
from threading import Lock

from synarmo.config import BackendName, SynarmoConfig, configured_model_path, load_env_file
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
        config = SynarmoConfig(
            profile=profile,
            backend=backend,
            model_path=configured_model_path(model_path),
            profiles_dir=Path(profiles_dir),
            **overrides,
        )
        memory = UserMemory.load(config.resolved_profile_dir(), profile)
        model_backend = create_backend(config)
        return cls(config=config, backend=model_backend, memory=memory)

    def configure(self, **updates: object) -> None:
        self.config = self.config.copy_with(**updates)
        self.context_assembler = ContextAssembler(max_chars=self.config.context_window * 2)

    def suggest(self, text: str, context: str | None = None) -> list[Suggestion]:
        assembled_context = self.context_assembler.assemble(
            text=text,
            context=context,
            memory=self.memory if self.config.style_adaptation else UserMemory(profile=self.config.profile),
        )
        generation_count = min(self.config.max_suggestions * 3, 10)
        generation_max_tokens = max(self.config.max_tokens, generation_count * 8)
        prompt = self.prompt_builder.build(
            assembled_context=assembled_context,
            max_suggestions=generation_count,
        )
        with self._generation_lock:
            raw = self.backend.generate(
                prompt,
                GenerationOptions(
                    max_tokens=generation_max_tokens,
                    temperature=self.config.temperature,
                    stop=self.config.stop,
                ),
            )
            ranked = self.ranker.rank(
                raw,
                current_text=text,
                max_suggestions=self.config.max_suggestions,
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
                                stop=self.config.stop,
                            ),
                        ),
                    ]
                )
        return self.ranker.rank(
            raw,
            current_text=text,
            max_suggestions=self.config.max_suggestions,
        )

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
    if _default_engine is None or _default_engine.config.profile != user_profile:
        _default_engine = SynarmoEngine.load(profile=user_profile, **load_options)
    return _default_engine.suggest(text=text, context=context)
