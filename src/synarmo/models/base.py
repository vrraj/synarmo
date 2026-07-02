from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    max_tokens: int = 32
    temperature: float = 0.25
    stop: list[str] = field(default_factory=list)


class ModelBackend(Protocol):
    name: str

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        raise NotImplementedError
