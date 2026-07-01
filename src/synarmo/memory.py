from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass(slots=True)
class UserMemory:
    profile: str = "default"
    style_summary: str = ""
    preferences: dict[str, str] = field(default_factory=dict)
    common_phrases: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, profile_dir: Path, profile: str) -> "UserMemory":
        path = profile_dir / "memory.json"
        if not path.exists():
            return cls(profile=profile)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self, profile_dir: Path) -> None:
        profile_dir.mkdir(parents=True, exist_ok=True)
        path = profile_dir / "memory.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
