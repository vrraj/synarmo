"""Reusable, user-managed compose context presets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ContextPreset:
    name: str
    text: str


class ContextPresetStore:
    """Read and write a deliberately small, human-editable YAML preset file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[ContextPreset]:
        if not self.path.exists():
            return []
        return self._parse(self.path.read_text(encoding="utf-8"))

    def save(self, name: str, text: str) -> ContextPreset:
        normalized_name = name.strip()
        normalized_text = text.strip()
        if not normalized_name:
            raise ValueError("A context preset needs a name.")
        if not normalized_text:
            raise ValueError("A context preset needs context text.")

        preset = ContextPreset(name=normalized_name, text=normalized_text)
        presets = [item for item in self.list() if item.name.casefold() != normalized_name.casefold()]
        presets.append(preset)
        presets.sort(key=lambda item: item.name.casefold())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self._serialize(presets), encoding="utf-8")
        return preset

    @staticmethod
    def _parse(source: str) -> list[ContextPreset]:
        presets: list[ContextPreset] = []
        current: dict[str, str] | None = None
        for raw_line in source.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line == "contexts:":
                continue
            if line.startswith("- "):
                if current is not None:
                    presets.append(ContextPresetStore._preset_from(current))
                current = {}
                line = line[2:].strip()
            if current is None or ":" not in line:
                raise ValueError("contexts.yaml must contain a list of name and text entries.")
            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            if key not in {"name", "text"}:
                raise ValueError("contexts.yaml entries may only contain name and text.")
            try:
                current[key] = json.loads(value.strip())
            except json.JSONDecodeError as exc:
                raise ValueError("Context names and text in contexts.yaml must use double quotes.") from exc
        if current is not None:
            presets.append(ContextPresetStore._preset_from(current))
        if len({item.name.casefold() for item in presets}) != len(presets):
            raise ValueError("Context preset names must be unique.")
        return presets

    @staticmethod
    def _preset_from(values: dict[str, str]) -> ContextPreset:
        if set(values) != {"name", "text"}:
            raise ValueError("Each contexts.yaml entry must contain name and text.")
        return ContextPreset(**values)

    @staticmethod
    def _serialize(presets: list[ContextPreset]) -> str:
        lines = ["# Reusable Synarmo context presets.", "contexts:"]
        for preset in presets:
            lines.extend(
                [
                    f"  - name: {json.dumps(preset.name, ensure_ascii=False)}",
                    f"    text: {json.dumps(preset.text, ensure_ascii=False)}",
                ]
            )
        return "\n".join(lines) + "\n"
