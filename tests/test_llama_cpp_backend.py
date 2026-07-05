import sys
import types

from synarmo.models.llama_cpp_backend import LlamaCppBackend


def test_llama_cpp_backend_uses_from_pretrained_for_repo_model(tmp_path, monkeypatch) -> None:
    calls = {}

    class FakeLlama:
        @classmethod
        def from_pretrained(cls, **kwargs):
            calls.update(kwargs)
            return cls()

        def __call__(self, *args, **kwargs):
            return {"choices": [{"text": "hello"}]}

    fake_module = types.SimpleNamespace(Llama=FakeLlama)
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
        "logits_all": True,
        "verbose": False,
    }
