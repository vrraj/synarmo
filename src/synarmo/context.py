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
        if len(assembled) <= self.max_chars:
            return assembled
        return self._trim_parts(parts)

    def _trim_parts(self, parts: list[str]) -> str:
        if self.max_chars < 1:
            return ""

        required = parts[-1]
        if len(required) >= self.max_chars:
            return _trim_labeled_part(required, self.max_chars)

        remaining = self.max_chars - len(required) - 1
        kept: list[str] = []
        for part in reversed(parts[:-1]):
            if remaining <= 0:
                break
            trimmed = _trim_labeled_part(part, remaining)
            if trimmed:
                kept.append(trimmed)
                remaining -= len(trimmed) + 1

        kept.reverse()
        kept.append(required)
        return "\n".join(kept)


def _trim_labeled_part(part: str, max_chars: int) -> str:
    if max_chars < 1:
        return ""
    if len(part) <= max_chars:
        return part
    if ": " not in part:
        return part[-max_chars:].lstrip()

    label, value = part.split(": ", 1)
    prefix = f"{label}: "
    if len(prefix) >= max_chars:
        return prefix[:max_chars].rstrip()

    value_budget = max_chars - len(prefix)
    return f"{prefix}{value[-value_budget:].lstrip()}"
