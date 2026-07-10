from __future__ import annotations

from synarmo.config import SynarmoConfig
from synarmo.models.base import ModelBackend
from synarmo.models.llama_cpp_backend import LlamaCppBackend
from synarmo.models.mock_backend import MockBackend


def create_backend(config: SynarmoConfig) -> ModelBackend:
    if config.backend == "mock":
        return MockBackend()
    if config.backend == "llama-cpp":
        return LlamaCppBackend(
            config.model_path,
            model_repo_id=config.model_repo_id,
            model_filename=config.model_filename,
            models_cache_dir=config.models_cache_dir,
            n_ctx=config.context_window,
            n_gpu_layers=config.n_gpu_layers,
        )
    raise ValueError(f"Unsupported backend: {config.backend}")
