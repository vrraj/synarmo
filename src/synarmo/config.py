from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

BackendName = Literal["mock", "llama-cpp"]

DEFAULT_MODELS_CACHE = Path("~/models/synarmo")
ENV_FILE = ".env"
LOCAL_MODELS_CACHE_ENV = "LOCAL_MODELS_CACHE"
MODEL_ENV = "SYNARMO_MODEL"
MODEL_PATH_ENV = "SYNARMO_MODEL_PATH"
MODEL_REPO_ID_ENV = "SYNARMO_MODEL_REPO_ID"
MAX_SUGGESTIONS_ENV = "SYNARMO_MAX_SUGGESTIONS"
MAX_TOKENS_ENV = "SYNARMO_MAX_TOKENS"
MAX_SUGGESTION_WORDS_ENV = "SYNARMO_MAX_SUGGESTION_WORDS"
TEMPERATURE_ENV = "SYNARMO_TEMPERATURE"
TOP_P_ENV = "SYNARMO_TOP_P"
LOGPROB_POOL_ENV = "SYNARMO_LOGPROB_POOL"
N_GPU_LAYERS_ENV = "SYNARMO_N_GPU_LAYERS"
LLAMA_VERBOSE_ENV = "SYNARMO_LLAMA_VERBOSE"


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

    value = _env_model()
    if value is None:
        return None

    value = value.expanduser()
    if value.is_absolute():
        return value
    return configured_models_cache() / value


def configured_model_filename(model_path: str | Path | None = None) -> str | None:
    if model_path:
        return Path(model_path).name

    value = _env_model()
    return value.name if value else None


def configured_model_repo_id() -> str | None:
    value = os.getenv(MODEL_REPO_ID_ENV)
    return value.strip() if value and value.strip() else None


def _env_model() -> Path | None:
    value = os.getenv(MODEL_ENV) or os.getenv(MODEL_PATH_ENV)
    return Path(value) if value else None


def configured_max_suggestions() -> int:
    value = os.getenv(MAX_SUGGESTIONS_ENV)
    return int(value) if value else 3


def configured_max_tokens() -> int:
    value = os.getenv(MAX_TOKENS_ENV)
    return int(value) if value else 5


def configured_max_suggestion_words() -> int:
    value = os.getenv(MAX_SUGGESTION_WORDS_ENV)
    return int(value) if value else 4


def configured_temperature() -> float:
    value = os.getenv(TEMPERATURE_ENV)
    return float(value) if value else 0.25


def configured_top_p() -> float:
    value = os.getenv(TOP_P_ENV)
    return float(value) if value else 0.95


def configured_logprob_pool() -> int:
    value = os.getenv(LOGPROB_POOL_ENV)
    return int(value) if value else 24


def configured_n_gpu_layers() -> int:
    value = os.getenv(N_GPU_LAYERS_ENV)
    return int(value) if value else 0


def configured_llama_verbose() -> bool:
    value = os.getenv(LLAMA_VERBOSE_ENV)
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class SynarmoConfig:
    backend: BackendName = "mock"
    model_path: Path | None = None
    model_repo_id: str | None = None
    model_filename: str | None = None
    models_cache_dir: Path = field(default_factory=configured_models_cache)
    profile: str = "default"
    max_suggestions: int = field(default_factory=configured_max_suggestions)
    max_latency_ms: int = 100
    context_window: int = 2048
    style_adaptation: bool = True
    temperature: float = field(default_factory=configured_temperature)
    top_p: float = field(default_factory=configured_top_p)
    max_tokens: int = field(default_factory=configured_max_tokens)
    max_suggestion_words: int = field(default_factory=configured_max_suggestion_words)
    logprob_pool: int = field(default_factory=configured_logprob_pool)
    n_gpu_layers: int = field(default_factory=configured_n_gpu_layers)
    llama_verbose: bool = field(default_factory=configured_llama_verbose)
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
        if not 0.0 < self.top_p <= 1.0:
            raise ValueError("top_p must be greater than 0.0 and at most 1.0")
        if not 1 <= self.max_tokens <= 128:
            raise ValueError("max_tokens must be between 1 and 128")
        if not 1 <= self.max_suggestion_words <= 20:
            raise ValueError("max_suggestion_words must be between 1 and 20")
        if not 1 <= self.logprob_pool <= 50:
            raise ValueError("logprob_pool must be between 1 and 50")
        if self.n_gpu_layers < -1:
            raise ValueError("n_gpu_layers must be -1 or greater")

    def resolved_profile_dir(self) -> Path:
        return self.profiles_dir.expanduser().resolve() / self.profile

    def copy_with(self, **updates: object) -> "SynarmoConfig":
        return replace(self, **updates)
