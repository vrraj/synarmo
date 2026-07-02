from synarmo.config import SynarmoConfig
from synarmo.engine import SynarmoEngine
from synarmo.memory import UserMemory
from synarmo.models import GenerationOptions


class FillBackend:
    name = "fill"

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return "have water"
        return "go outside\ntake a walk\nneed help"


def test_engine_fill_pass_runs_when_cleanup_leaves_too_few_suggestions(tmp_path) -> None:
    backend = FillBackend()
    engine = SynarmoEngine(
        config=SynarmoConfig(max_suggestions=3, profiles_dir=tmp_path),
        backend=backend,
        memory=UserMemory(profile="test"),
    )

    suggestions = engine.suggest("I want to", context="At home")

    assert len(backend.prompts) == 2
    assert "Alternatives:" in backend.prompts[1]
    assert [item.text for item in suggestions] == ["have water", "go outside", "need help"]
