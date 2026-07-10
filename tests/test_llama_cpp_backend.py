import sys
import types

from synarmo.models.base import GenerationOptions
from synarmo.models.llama_cpp_backend import LlamaCppBackend


def fake_llama_cpp_module(*, supports_gpu_offload: bool = False, model_layers: int = 16):
    return types.SimpleNamespace(
        llama_supports_gpu_offload=lambda: supports_gpu_offload,
        llama_model_n_layer=lambda model: model_layers,
    )


def test_llama_cpp_backend_uses_from_pretrained_for_repo_model(tmp_path, monkeypatch) -> None:
    calls = {}

    class FakeLlama:
        @classmethod
        def from_pretrained(cls, **kwargs):
            calls.update(kwargs)
            return cls()

        def __call__(self, *args, **kwargs):
            return {"choices": [{"text": "hello"}]}

    fake_module = types.SimpleNamespace(Llama=FakeLlama, llama_cpp=fake_llama_cpp_module())
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    LlamaCppBackend(
        None,
        model_repo_id="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        model_filename="llama-3.2-1b-instruct-q4_k_m.gguf",
        models_cache_dir=tmp_path,
        n_ctx=1024,
    )

    assert calls == {
        "repo_id": "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        "filename": "llama-3.2-1b-instruct-q4_k_m.gguf",
        "local_dir": str(tmp_path),
        "n_ctx": 1024,
        "n_gpu_layers": 0,
        "logits_all": True,
        "verbose": False,
    }


def test_llama_cpp_backend_generate_passes_sampling_options(tmp_path, monkeypatch) -> None:
    calls = {}

    class FakeLlama:
        def __init__(self, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            calls.update(kwargs)
            return {"choices": [{"text": "hello"}]}

    model_path = tmp_path / "model.gguf"
    model_path.write_text("", encoding="utf-8")
    fake_module = types.SimpleNamespace(Llama=FakeLlama, llama_cpp=fake_llama_cpp_module())
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    backend = LlamaCppBackend(model_path)
    backend.generate(
        "prompt",
        GenerationOptions(max_tokens=7, temperature=0.4, top_p=0.8, stop=["\n"]),
    )

    assert calls == {
        "max_tokens": 7,
        "temperature": 0.4,
        "top_p": 0.8,
        "stop": ["\n"],
    }


def test_llama_cpp_backend_passes_gpu_layers_to_local_model(tmp_path, monkeypatch) -> None:
    calls = {}

    class FakeLlama:
        def __init__(self, **kwargs):
            calls.update(kwargs)

        def __call__(self, *args, **kwargs):
            return {"choices": [{"text": "hello"}]}

    model_path = tmp_path / "model.gguf"
    model_path.write_text("", encoding="utf-8")
    fake_module = types.SimpleNamespace(
        Llama=FakeLlama,
        llama_cpp=fake_llama_cpp_module(supports_gpu_offload=True),
    )
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_module)

    backend = LlamaCppBackend(model_path, n_gpu_layers=-1, verbose=True)

    assert calls["n_gpu_layers"] == -1
    assert calls["verbose"] is True
    assert backend.diagnostics() == {
        "n_gpu_layers": -1,
        "requested_gpu_layers": "all",
        "gpu_offload_supported": True,
        "llama_verbose": True,
    }
