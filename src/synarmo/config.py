from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

BackendName = Literal["mock", "llama-cpp"]

DEFAULT_MODELS_CACHE = Path("~/models/synarmo")
ENV_FILE = ".env"
LOCAL_MODELS_CACHE_ENV = "LOCAL_MODELS_CACHE"
MODEL_PATH_ENV = "SYNARMO_MODEL_PATH"
MAX_SUGGESTIONS_ENV = "SYNARMO_MAX_SUGGESTIONS"


def load_env_file(path: str | Path = ENV_FILE) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def configured_models_cache() -> Path:
    value = os.getenv(LOCAL_MODELS_CACHE_ENV)
    return Path(value).expanduser() if value else DEFAULT_MODELS_CACHE.expanduser()


def configured_model_path(model_path: str | Path | None = None) -> Path | None:
    if model_path:
        return Path(model_path).expanduser()

    value = _env_model_path()
    if value is None:
        return None

    value = value.expanduser()
    if value.is_absolute():
        return value
    return configured_models_cache() / value


def _env_model_path() -> Path | None:
    value = os.getenv(MODEL_PATH_ENV)
    return Path(value) if value else None


def configured_max_suggestions() -> int:
    value = os.getenv(MAX_SUGGESTIONS_ENV)
    return int(value) if value else 3


@dataclass(slots=True)
class SynarmoConfig:
    backend: BackendName = "mock"
    model_path: Path | None = None
    models_cache_dir: Path = field(default_factory=configured_models_cache)
    profile: str = "default"
    max_suggestions: int = field(default_factory=configured_max_suggestions)
    max_latency_ms: int = 100
    context_window: int = 2048
    style_adaptation: bool = True
    temperature: float = 0.25
    max_tokens: int = 32
    stop: list[str] = field(default_factory=lambda: ["\n\n"])
    profiles_dir: Path = Path("profiles")

    def __post_init__(self) -> None:
        self.models_cache_dir = self.models_cache_dir.expanduser()
        if self.model_path is not None:
            self.model_path = self.model_path.expanduser()
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
