from concurrent.futures import ThreadPoolExecutor
from time import sleep

from synarmo.config import SynarmoConfig
from synarmo.engine import SynarmoEngine
from synarmo.memory import UserMemory
from synarmo.models import GenerationOptions


class LockedBackend:
    name = "locked"

    def __init__(self) -> None:
        self.active_calls = 0
        self.max_active_calls = 0

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        self.active_calls += 1
        self.max_active_calls = max(self.max_active_calls, self.active_calls)
        sleep(0.01)
        self.active_calls -= 1
        return "have water\ngo outside\ntake a walk"


def test_engine_serializes_backend_generation(tmp_path) -> None:
    backend = LockedBackend()
    engine = SynarmoEngine(
        config=SynarmoConfig(max_suggestions=3, profiles_dir=tmp_path),
        backend=backend,
        memory=UserMemory(profile="test"),
    )

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(
            executor.map(
                lambda text: engine.suggest(text, context="At home"),
                ["I want to", "Can you", "Please"],
            )
        )

    assert all(result for result in results)
    assert backend.max_active_calls == 1
