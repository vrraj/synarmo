from __future__ import annotations

from synarmo.config import SynarmoConfig
from synarmo.models.base import ModelBackend
from synarmo.models.llama_cpp_backend import LlamaCppBackend
from synarmo.models.mock_backend import MockBackend


def create_backend(config: SynarmoConfig) -> ModelBackend:
    if config.backend == "mock":
        return MockBackend()
    if config.backend == "llama-cpp":
        if config.model_path is None:
            raise ValueError("model_path is required for the llama-cpp backend")
        return LlamaCppBackend(config.model_path, n_ctx=config.context_window)
    raise ValueError(f"Unsupported backend: {config.backend}")
