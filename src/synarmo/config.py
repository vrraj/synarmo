from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

BackendName = Literal["mock", "llama-cpp"]


@dataclass(slots=True)
class SynarmoConfig:
    backend: BackendName = "mock"
    model_path: Path | None = None
    profile: str = "default"
    max_suggestions: int = 4
    max_latency_ms: int = 100
    context_window: int = 2048
    style_adaptation: bool = True
    temperature: float = 0.25
    max_tokens: int = 32
    stop: list[str] = field(default_factory=lambda: ["\n", ".", "!", "?"])
    profiles_dir: Path = Path("profiles")

    def __post_init__(self) -> None:
        if not 1 <= self.max_suggestions <= 10:
            raise ValueError("max_suggestions must be between 1 and 10")
        if self.max_latency_ms < 1:
            raise ValueError("max_latency_ms must be positive")
        if self.context_window < 128:
            raise ValueError("context_window must be at least 128")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        if not 1 <= self.max_tokens <= 128:
            raise ValueError("max_tokens must be between 1 and 128")

    def resolved_profile_dir(self) -> Path:
        return self.profiles_dir.expanduser().resolve() / self.profile

    def copy_with(self, **updates: object) -> "SynarmoConfig":
        return replace(self, **updates)
