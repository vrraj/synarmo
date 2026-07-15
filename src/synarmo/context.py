from __future__ import annotations

from dataclasses import dataclass

from synarmo.memory import UserMemory


@dataclass(slots=True)
class ContextAssembler:
    max_chars: int = 4000

    def assemble(self, *, text: str, context: str | None, memory: UserMemory) -> str:
        parts: list[str] = []
        if memory.style_summary:
            parts.append(f"User style: {memory.style_summary}")
        if memory.preferences:
            prefs = "; ".join(f"{key}: {value}" for key, value in sorted(memory.preferences.items()))
            parts.append(f"Known preferences: {prefs}")
        if context:
            parts.append(f"Current context: {context.strip()}")
        parts.append(f"Current typed text: {text.strip()}")
        assembled = "\n".join(part for part in parts if part)
        return assembled[-self.max_chars :]
