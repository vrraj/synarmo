from synarmo.config import SynarmoConfig
from synarmo.engine import SynarmoEngine
from synarmo.memory import UserMemory
from synarmo.models import GenerationOptions


class RecordingBackend:
    name = "recording"

    def __init__(self) -> None:
        self.prompt = ""
        self.options: GenerationOptions | None = None

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        self.prompt = prompt
        self.options = options
        return "go outside\nhave water\ntake a walk\nrest now"


def test_engine_overgenerates_then_returns_configured_count(tmp_path) -> None:
    backend = RecordingBackend()
    engine = SynarmoEngine(
        config=SynarmoConfig(max_suggestions=3, top_p=0.95, profiles_dir=tmp_path),
        backend=backend,
        memory=UserMemory(profile="test"),
    )

    suggestions = engine.suggest("I want to", context="At home")

    assert backend.prompt == "Current context: At home\n\nI want to"
    assert backend.options is not None
    assert backend.options.max_tokens == 72
    assert backend.options.top_p == 0.95
    assert len(suggestions) == 3
